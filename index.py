#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals # polskie znaki
import pygame
import os
import json
import threading
import time
from gpiozero import Button
from ina219 import INA219
pygame.init()

#--------------------DEV/PRODUKCJA-----------------------------------------------------------#
#       Zakomentuj odpowiednie wiersze aby uruchomic program na komputerze / raspberry       
# -------------------------------------------------------------------------------------------#

#----Raspberry-----
screen = pygame.display.set_mode([320, 480], pygame.FULLSCREEN)  # Definiowanie okna
pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0)) # Usuwanie kursora

#----DEV-----------
#screen = pygame.display.set_mode([320, 480])


#--------------------ZMIENNE GLOBALNE------------------------------------------------------------
source = os.path.join(os.path.dirname(__file__), 'logo.png') # Ladowanie logo
logo = pygame.image.load(source)

route = '1'                 # Zmienna pod-menu
keyboard = (False, False)   # Pierwszy parametr - klawiatura QWERTY, drugi parametr - klawiatura numeryczna
keyboard_upper = False      # Zmienna SHIFT
k_number = ''               # Zmienna wprowadzanego numeru
k_text = ''                 # Zmienna wprowadzanego tekstu

k_number_display = []       # Zmienne pomocnicze do wyswitlania tesktu/numeru dla klawiatur
k_number_tmp = ''
k_text_display = []
k_text_tmp = ''

keyboardArray = [           # Tablica znaków
    ['0','1','2','3','4','5','6','7','8','9','q','w','e','r','t','y','u','i','o','p','a','s','d','f','g','h','i','j','k','l','z','x','c','v','b','n','m','.',',','?'],
    ['1','2','3','+','4','5','6','#','7','8','9','0']
]

running = True              # Zmienna petli

with open('kontakty.txt') as file:     # pobieranie bazy kontaktów
    kontakty = json.load(file)         # Obiekt kontakty

with open('odebrane.txt') as file:     # pobieranie ODEBRANYCH sms-ów
    odebrane = json.load(file)         # Obiekt smsy

with open('wyslane.txt') as file:      # pobieranie WYSLANYCH sms-ów
    wyslane = json.load(file)          # Obiekt smsy

wyslane_strona = 0                     # Strony wyswietlania smsow/kontaktow
odebrane_strona = 0
kontakty_strona = 0

button = Button(26)                    # GPIO do Buttona
ScreenSleep = False                    # Wygaszanie ekranu

SHUNT_OHMS = 0.1                       # Konfiguracja INA (pomiar napiecia)
MAX_EXPECTED_AMPS = 1
ina = INA219(SHUNT_OHMS, MAX_EXPECTED_AMPS)
ina.configure(ina.RANGE_16V)

napiecie = round(ina.voltage(),2)
poziomNaladowania = int((ina.voltage()-3.5)*143)

#--------------------KlASY / FUNKCJE------------------------------------------------------------

def center_szerokosc(slowo_lub_zdanie, rozmiar_czcionki, szerokosc = 320):           # centrowanie slowa/zdania pionowo
    return (szerokosc - pygame.font.Font(None, rozmiar_czcionki).size(slowo_lub_zdanie)[0])/2

def zeruj():      # usuwanie wartosci zmiennych globalnych numeru telefonu i tresci wiadomosci oraz ich odpowiednikow odpowiedzialnych za wyswitlanie
    global k_text, k_text_tmp, k_number_display, k_number, k_number_tmp, k_number_display
    k_text = ''
    k_text_tmp = ''
    k_number_display = []
    
    k_number = ''
    k_number_tmp = ''
    k_number_display = []

class Circle:       # Rysowanie okregow
    def __init__(self, sx, sy, diameter):
        self.sx = sx
        self.sy = sy
        self.diameter = diameter
        self.colour = (255, 255, 255)
        self.thickness = 1

    def display(self):
        pygame.draw.circle(screen, self.colour, (self.sx, self.sy), self.diameter, self.thickness)

class Text:         # Rysowanie tekstu
    def __init__(self, sx, sy, text, size):
        self.sx = sx
        self.sy = sy
        self.text = text
        self.size = size
        self.textsurface = pygame.font.SysFont('Chandas', self.size).render(self.text, True, (255, 255, 255))
    def display(self):
        screen.blit(self.textsurface,(self.sx, self.sy))

class KeyboardInput: # Rysowanie znakow klawiatury (prostokaty + znaki)
    def __init__(self, sx, sy, text, upper_case, sizex = 32, sizey = 40, textx = 10, texty = 10, textsize = 30):
        self.sx = sx
        self.sy = sy
        self.sizex = sizex
        self.sizey = sizey
        self.textx = textx
        self.texty = texty
        self.size = 20 if text=='SHIFT' or text=="SPACJA" or text==u"WYŚLIJ" or text==u"USUŃ" or text==u"WRÓĆ" or text == "DODAJ" else textsize
        self.text = text.upper() if upper_case else text
        self.textsurface = pygame.font.SysFont('Chandas', self.size).render(self.text, True, (255, 255, 255))
    def display(self):
        screen.blit(self.textsurface,(self.sx + self.textx, self.sy + self.texty))
        if self.text == "SHIFT":
            pygame.draw.rect(screen, (255,255,255), (self.sx,self.sy,60,40), 1)
        elif self.text == "SPACJA":
            pygame.draw.rect(screen, (255,255,255), (self.sx,self.sy,70,40), 1)
        elif self.text == u"WYŚLIJ" or self.text == "DODAJ":
            pygame.draw.rect(screen, (255,255,255), (self.sx,self.sy,70,40), 1)
        elif self.text == u"USUŃ":
            pygame.draw.rect(screen, (255,255,255), (self.sx,self.sy,60,40), 1)
        elif self.text == u"WRÓĆ":
            pygame.draw.rect(screen, (255,255,255), (self.sx,self.sy,60,40), 1)
        else:
            pygame.draw.rect(screen, (255,255,255), (self.sx, self.sy, self.sizex, self.sizey), 1)

#--------------------OBIEKTY MENU------------------------------------------------------------

mainArray = [       # Obiekty głównego menu
    Circle(160, 175, 50), Text(center_szerokosc('POŁACZENIA', 20),170,'POŁĄCZENIA', 20),
    Circle(160, 305, 50), Text(center_szerokosc('SMS', 20),300,'SMS', 20),
]
callArray = [       # Obiekty sub-menu dzwonienia
    Circle(95, 175, 50), Text(center_szerokosc('WYBIERZ', 20, 160)+15,160,'WYBIERZ', 20), Text(center_szerokosc('NUMER', 20, 160)+15,180,'NUMER', 20),
    Circle(225, 175, 50), Text(center_szerokosc('KONTAKTY', 20,160) + 145,170,'KONTAKTY', 20),
    Circle(95, 305, 50), Text(center_szerokosc('DODAJ', 20, 160)+15, 290,'DODAJ', 20), Text(center_szerokosc('KONTAKT', 20, 160)+15,310,'KONTAKT', 20),
    Circle(225, 305, 50), Text(center_szerokosc('USUŃ', 20, 160) + 145, 290,'USUN', 20), Text(center_szerokosc('KONTAKT', 20, 160) + 145,310,'KONTAKT', 20),
    Text(center_szerokosc('POWROT', 20),450,'POWROT', 20),
]
smsArray = [        # Obiekty sub-menu sms
    Circle(95, 175, 50), Text(center_szerokosc('NOWA', 20, 160)+15,160,'NOWA', 20), Text(center_szerokosc('WIADOMOŚĆ', 20, 160)+15,180,'WIADOMOŚĆ', 20),
    Circle(225, 175, 50), Text(center_szerokosc('KONTAKTY', 20,160) + 145,170,'KONTAKTY', 20),
    Circle(95, 305, 50), Text(center_szerokosc('WIADOMOŚCI', 20, 160)+15, 290,'WIADOMOŚCI', 20), Text(center_szerokosc('ODEBRANE', 20, 160)+15,310,'ODEBRANE', 20),
    Circle(225, 305, 50), Text(center_szerokosc('WIADOMOŚCI', 20, 160) + 145, 290,'WIADOMOŚCI', 20), Text(center_szerokosc('WYSŁANE', 20, 160) + 145,310,'WYSŁANE', 20),
    Text(center_szerokosc('POWRÓT', 20),450,'POWRÓT', 20),
]

#--------------------GLOWNA PETLA------------------------------------------------------------
timer = time.time()  # Inicjalizacja timera
while running:

    if time.time() - timer > 10:                        # co 10 sekund sprawdzaj napięcie zasilania
            timer = time.time()
            napiecie = round(ina.voltage(),2)
            poziomNaladowania = int((ina.voltage()-3.5)*143)  # min napiecie - 3.5V

    if button.is_pressed:
        time.sleep(.1)
        button.wait_for_release()
        ScreenSleep = not ScreenSleep
        pygame.event.clear()
        if ScreenSleep == True:
            screen.fill((0, 0, 0))
            pygame.display.update()
    elif ScreenSleep == False:

        screen.fill((30, 30, 30))   # Kolor tła
        screen.blit(logo, (0, 80))  # logo

    #~~~~~~~~~~~~~~~~~~EVENT HANDLER + ROUTING~~~~~~~~~~~~~~~~~
    
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYUP: # eventy wyjscia z programu
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:      # Event -> dotyk
                x, y = pygame.mouse.get_pos()               # Pobierz koordynaty dotkniecia
                if route == '1':                            # Handler glownego menu
                    if x >= 110 and x<=210 and y>=125 and y<=225:          # polaczenia
                        route = '11'
                    elif x >= 110 and x<=210 and y>=255 and y<=355:        # sms
                        route = '12'

                elif route == '11':                         # Handler sub-menu dzwonienia
                    if x >= 45 and x<=145 and y>=125 and y<=225:            # Wybierz numer
                        route = '111'
                    elif x >= 175 and x<=275 and y>=125 and y<=225:         # Kontakty
                        route = '112'
                    elif x >= 45 and x<=145 and y>=255 and y<=355:          # Dodaj numer
                        route = '113'
                    elif x >= 175 and x<=275 and y>=255 and y<=355:         # Usuń numer
                        route = '114'
                    elif x >= 0 and x<=320 and y>=430 and y<=480:           # Powrot
                        route = route[:-1]

                elif route == '12':                         # Handler sub-menu sms
                    if x >= 45 and x<=145 and y>=125 and y<=225:            # Nowa wiadomosc
                        route = '121'
                    if x >= 175 and x<=275 and y>=125 and y<=225:          # Kontakty
                        route = '122'
                    if x >= 45 and x<=145 and y>=255 and y<=355:           # wiadomosci odebrane
                        route = '123'
                    if x >= 175 and x<=275 and y>=255 and y<=355:           # wiadomosci wyslane
                        route = '124'
                    if x >= 0 and x<=320 and y>=430 and y<=480:             # Powrot
                        route = route[:-1]
                
                elif route == '112' or route == '122' or route == "114" or route == '123' or route == '124':   # Kontakty/historiaSMS/usuwanie kontaktu - jedno GUI
                    if x>0 and x<320 and y>440 and y<480:             # Powrot
                        route = route[:-1]
                        wyslane_strona = 0
                        odebrane_strona = 0
                    elif x>160 and x<320 and y>400 and y<440:      # Nastepna strona
                        if route == '124' and wyslane_strona + 1 < wyslane['number']/8:
                            wyslane_strona = wyslane_strona + 1
                        elif route == '123' and odebrane_strona + 1 < odebrane['number']/8:
                            odebrane_strona = odebrane_strona + 1
                        elif route == '112' or route == '114' or route == '122':
                            if kontakty_strona + 1 < kontakty['number']/8:
                                kontakty_strona = kontakty_strona + 1
                    elif x>0 and x<160 and y>400 and y<440:      # Poprzednia strona
                        if route == '124' and wyslane_strona>0:
                            wyslane_strona = wyslane_strona - 1
                        elif route == '123' and odebrane_strona>0:
                            odebrane_strona = odebrane_strona - 1
                        elif route == '112' or route == '114' or route == '122':
                            if kontakty_strona>0:
                                kontakty_strona = kontakty_strona - 1
                    elif route == '112':           # Dzwonienie pod wybrany z listy kontaktow numer
                        for i in range(0,8):
                            if kontakty['number'] - (i + kontakty_strona*8) > 0 and x>0 and x<320 and y>50*i and y<50*(i+1):
                                k_number = kontakty[str(kontakty['number'] - kontakty_strona*8 - i)]['tel']
                                route = '1111'
                    elif route == '122':            # Pisanie SMS pod wybrany z listy kontaktow numer                             
                        for i in range(0,8):
                            if kontakty['number'] - (i + kontakty_strona*8) > 0 and x>0 and x<320 and y>50*i and y<50*(i+1):
                                k_number = kontakty[str(kontakty['number'] - kontakty_strona*8 - i)]['tel']
                                route = '1211'
                    elif route == '114':
                        for i in range(0,8):
                            if kontakty['number'] - (i + kontakty_strona*8) > 0 and x>0 and x<320 and y>50*i and y<50*(i+1):
                                route = route + '1' + str(kontakty['number']-kontakty_strona*8 -i)
                    elif route == '123':                    # SZCZEGOLY WIADOMOSCI ODEBRANYCH
                        for i in range(0,8):
                            if odebrane['number'] - (i + odebrane_strona*8) > 0 and x>0 and x<320 and y>50*i and y<50*(i+1):
                                route = route + '1' + str(odebrane['number']-odebrane_strona*8 -i)
                    elif route == '124':                    # SZCZEGOLY WIADOMOSCI WYSLANYCH
                        for i in range(0,8):
                            if wyslane['number'] - (i + wyslane_strona*8) > 0 and x>0 and x<320 and y>50*i and y<50*(i+1):
                                route = route + '1' + str(wyslane['number']-wyslane_strona*8 -i)

                elif route[:4] == '1231' or route[:4] == '1241':
                    if x >= 0 and x<=320 and y>=430 and y<=480:             # Powrot z szczegolow smsów
                        route = route[:4][:-1]
                elif route[:4] == '1141':           # usuwanie kontaktu
                    if x>30 and x<130 and y>325 and y<425:
                        numer = route[4:]
                        for x in range (int(numer), kontakty['number']):  # Funckja przesuwania dicta w lewo od odpowiedniego id
                            kontakty[str(x)].update({'tel': kontakty[str(x+1)]['tel'], 'text': kontakty[str(x+1)]['text']})
                        kontakty.pop(str(kontakty["number"]))
                        kontakty['number'] = kontakty["number"] - 1
                        with open('kontakty.txt', 'w') as file:
                            json.dump(kontakty, file)
                        route = '11'
                    elif x>190 and x<290 and y>325 and y<425:
                        route = '11'
                elif route == '1111':                       # widok połaczenia
                    if x >= 110 and x<=210 and y>=350 and y<=450:             # Powrot
                        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                        #                                                           
                        #  Tutaj zaimplementuj wysylanie zadania anulowania polaczenia
                        #                                                             
                        #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                        zeruj()
                        route = '11'
                
                if keyboard[0]:                             # Handler klawiatury QWERTY
                    kx = 0
                    ky = 280
                    for letter in keyboardArray[0]:
                        if x>=kx and x<kx+32 and y>=ky and y<ky+40:
                            k_text = k_text + letter.upper() if keyboard_upper else k_text + letter # zmienna do Sim800
                            k_text_tmp = k_text_tmp + letter.upper() if keyboard_upper else k_text_tmp + letter # Wyświetlanie
                            if pygame.font.Font(None, 20).size(k_text_tmp)[0] >= 190:
                                k_text_display.append(k_text_tmp)
                                k_text_tmp = ''
                        kx = kx + 32
                        if kx == 320:
                            kx = 0
                            ky = ky + 40
                    if x>=0 and x<=60 and y>=440 and y<=480:
                        keyboard_upper = False if keyboard_upper else True
                    if x>=60 and x<=130 and y>=440 and y<=480:
                        k_text = k_text + ' '
                        k_text_tmp = k_text_tmp + ' '
                    if x>=130 and x<=200 and y>=440 and y<=480 and k_text != '':
                        keyboard_upper = False
                        keyboard = (False, False)
                        if route == '1211':
                            #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                            #  Zmienne: (string) k_number -> numer telefonu      
                            #           (string) k_text -> tekst wiadomosci      
                            #  Tutaj wpisac polecenie wysylania SMSa na SIM800  
                            #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
                            wyslane[str(wyslane['number']+1)] = {"tel": k_number, "text": k_text}  #zapis wyslanego smsa
                            wyslane['number'] = wyslane['number'] + 1
                            with open('wyslane.txt', 'w') as file:
                                json.dump(wyslane, file)
                            route = route + '1'         # route = 12111 -> ekran wysylania smsa
                        elif route == '1131':           # !!! zapis nowego kontaktu do pliku
                            Found = False
                            for key in kontakty: # Sprawdz czy kontakt istnieje, jezeli tak, to nadpisz nazwe
                                if isinstance(kontakty[key], int) == False and kontakty[key]['tel'][-9:] == k_number:
                                    kontakty[key] = {"tel": k_number, "text": k_text}
                                    with open('kontakty.txt', 'w') as file:
                                        json.dump(kontakty, file)
                                    zeruj()
                                    Found = True
                            if Found == False:
                                kontakty[str(kontakty['number']+1)] = {"tel": k_number, "text": k_text}
                                kontakty['number'] = int(kontakty['number'] + 1)
                                with open('kontakty.txt', 'w') as file:
                                    json.dump(kontakty, file)
                                zeruj()
                            route = route + '1'        # route 11311 -> ekran dodania kontatku
                    if x>=200 and x<=260 and y>=440 and y<=480:
                        k_text = k_text[:-1]
                        if len(k_text_tmp) == 0 and k_text_display:
                            if(len(k_text_display[-1]) == 0):
                                k_text_display = k_text_display[:-1]
                            else:
                                k_text_display[-1] = k_text_display[-1][:-1]
                        else:
                            k_text_tmp = k_text_tmp[:-1]
                        
                    if x>=260 and x<=320 and y>=440 and y<=480:
                        keyboard = (False, False)
                        keyboard_upper = False
                        k_text = ''                     # Funcka zeruj() nie zostala uzyta aby numer telefonu sie zachowal przy przejsciu numer -> tresc w tworzonym smsie
                        k_text_tmp = ''
                        k_text_display = []
                        route = route[:-1]
                
                elif keyboard[1]:                       # Handler klawiatury numerycznej
                    kx = 0
                    ky = 200
                    for number in keyboardArray[1]:
                        if x>=kx and x<kx+80 and y>=ky and y<ky+80:
                            k_number = k_number + number
                            k_number_tmp = k_number_tmp + number # Wyswietlanie
                            if pygame.font.Font(None, 20).size(k_number_tmp)[0] >= 85:
                                k_number_display.append(k_number_tmp)
                                k_number_tmp = ''
                        kx = kx + 80
                        if kx == 320:
                            kx = 0
                            ky = ky + 80
                    if x>=0 and x<=100 and y>=440 and y<=480:
                        k_number = k_number[:-1]
                        if len(k_number_tmp) == 0 and k_number_display:
                            if len(k_number_display[-1]) == 0:
                                k_number_display = k_number_display[:-1]
                            else:
                                k_number_display[-1] = k_number_display[-1][:-1]
                        else:
                            k_number_tmp = k_number_tmp[:-1]
                    elif x>=100 and x<=220 and y>=440 and y<=480 and k_number != '':
                        keyboard = (False, False)
                        if route == '111': route = route + '1'    # route = '1111'  ->   ekran dzwonienia
                            #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#
                            #  Zmienne: (string) k_number -> numer telefonu                    
                            #                                                                  
                            #  Tutaj wpisac polecenie rządania wykonania połaczenia na SIM800  
                            #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%#
                        elif route == '121': route = route + '1'  # przejdz do tresci smsa po wybraniu numeru
                        elif route == '113': route = route + '1'
                    elif x>=220 and x<=320 and y>=440 and y<=480:
                        keyboard = (False, False)
                        zeruj()
                        route = route[:-1]
                    
    #~~~~~~~~~~~~~~~~~~RENDEROWANIE OBIEKTOW~~~~~~~~~~~~~~~~~~

        if route == '1':                               # Głowne menu
            for element in mainArray:
                element.display()
            Text(center_szerokosc('Zasilanie:   '+str(napiecie)+' V   '+str(poziomNaladowania)+' %',30), 20,'Zasilanie:   '+str(napiecie)+' V   '+str(poziomNaladowania)+' %',30).display()
        elif route == '11':                            # Dzwonienie
            for element in callArray:
                element.display()
            Text(center_szerokosc('Zasilanie:   '+str(napiecie)+' V   '+str(poziomNaladowania)+' %',30), 20,'Zasilanie:   '+str(napiecie)+' V   '+str(poziomNaladowania)+' %',30).display()
        elif route == '12':                            # Sms
            for element in smsArray:
                element.display()
            Text(center_szerokosc('Zasilanie:   '+str(napiecie)+' V   '+str(poziomNaladowania)+' %',30), 20,'Zasilanie:   '+str(napiecie)+' V   '+str(poziomNaladowania)+' %',30).display()
        elif route == '111' or route == '121' or route == '113':         # Wybieranie numeru - nowe polaczenie/nowy sms - nowy numer
            keyboard = (False, True)
            ky = 40
            if(len(k_number_display) == 0):
                Text(10, ky, k_number_tmp, 60).display()
            else:
                for line in k_number_display:
                    Text(10, ky, line, 60).display()
                    ky = ky + 40
                Text(10, ky, k_number_tmp, 60).display()
        elif route == '1111':
            keyboard = (False, False)
            notFound = True
            for key in kontakty:
                if isinstance(kontakty[key], int) == False and kontakty[key]['tel'][-9:] == k_number[-9:]:
                    Text(center_szerokosc(kontakty[key]['text'][-9:], 20),100, kontakty[key]['text'][-9:], 20).display()
                    notFound = False
            if notFound: Text(center_szerokosc('NIEZNANY', 20),100, 'NIEZNANY', 20).display()
            Text(center_szerokosc(k_number, 40),120, k_number, 40).display()
            Text(center_szerokosc('DZWONIENIE', 40),200,'DZWONIENIE', 40).display()
            Circle(160,400,50).display()
            Text(center_szerokosc('ZAKOŃCZ', 25),390,'ZAKOŃCZ', 25).display()

        elif route == '1211' or route == '1131':                            # Pisanie SMS - nowy sms - tresc
            keyboard = (True, False)
            ky = 10
            if(len(k_text_display) == 0):
                Text(10, ky, k_text_tmp, 30).display()
            else:
                for line in k_text_display:
                    Text(10, ky, line, 30).display()
                    ky = ky + 30
                Text(10, ky, k_text_tmp, 30).display()
    #---------FINALIZACJA SMS------------------------

        elif route == '12111':                         # Finalizacja SMS
            keyboard = (False, False)
            Text(center_szerokosc('WYSYŁANIE', 40),240,'WYSYŁANIE...', 40).display()
            route = route + '1'
        elif route == '121111':                        # Mozna zaimplementować callbacka z sim800 o sukces zamiast waita
            pygame.time.wait(1000)   
            route = route + '1'
        elif route == '1211111':
            Text(center_szerokosc('SUKCES!', 40),240,'SUKCES!', 40).display()
            route = route + '1'
        elif route == '12111111':
            zeruj()
            pygame.time.wait(1000)
            route = '12'
        #------------------------------------------------
        #------FINALIZACJA ZAPISYWANIA NUMERU------------
        elif route == '11311':
            keyboard = (False, False)
            Text(center_szerokosc('ZAPISANO!', 40),240,'ZAPISANO!', 40).display()
            route = route + '1'
        elif route == '113111':
            pygame.time.wait(1000)
            zeruj()
            route = '11'
        #---------------------------------------------------

        elif route == '112' or route == '122' or route == '114' or route == '123' or route == '124': # GUI dla listy
            KeyboardInput(0, 400, 'POPRZEDNIA', False, 160, 40, center_szerokosc('POPRZEDNIA', 30, 160), 10, 30).display()
            KeyboardInput(160, 400, 'NASTĘPNA', False, 160, 40, center_szerokosc('NASTĘPNA', 30, 160), 10, 30).display()
            KeyboardInput(0, 440, u"POWRÓT", False, 320, 40, center_szerokosc('POWRÓT', 30), 10, 30).display()
            if route == '112' or route == '122' or route == '114':
                ky = 0
                for key in range(kontakty["number"], 0, -1): #wyswietlanie kontaktow
                    if isinstance(kontakty[str(key)], int) == False and float(key)<=kontakty['number']-(kontakty_strona*8) and float(key)>(kontakty['number']-(kontakty_strona*8))-8:
                        if len(kontakty[str(key)]['text']) > 30: i = '...'
                        else: i = ''
                        Text(center_szerokosc(kontakty[str(key)]['text'][:30] + i, 25), ky+7, kontakty[str(key)]['text'][:30] + i, 25).display()
                        KeyboardInput(0,ky, kontakty[str(key)]['tel'][-9:], False, 320,50,center_szerokosc(kontakty[str(key)]['tel'][-9:],25),28,25).display()
                        ky = ky + 50  
            elif route == '123': # wyświetlanie odebranych smsów
                ky = 0
                for key in range(odebrane["number"], 0, -1):
                    if isinstance(odebrane[str(key)], int) == False and float(key)<=odebrane['number']-(odebrane_strona*8) and float(key)>(odebrane['number']-(odebrane_strona*8))-8:
                        if len(odebrane[str(key)]['text']) > 30: i = '...'
                        else: i = ''
                        notFound = True
                        for key2 in kontakty:
                            if isinstance(kontakty[key2], int) == False and kontakty[key2]['tel'][-9:] == odebrane[str(key)]['tel'][-9:]:
                                KeyboardInput(0,ky, kontakty[key2]['text'], False, 320,50,center_szerokosc(kontakty[key2]['text'],25),7,25).display()
                                notFound = False
                        if notFound: KeyboardInput(0,ky, wyslane[str(key)]['tel'][-9:], False, 320,50,center_szerokosc(wyslane[str(key)]['tel'][-9:],25),7,25).display()
                        Text(center_szerokosc(odebrane[str(key)]['text'][:30] + i, 25), ky+28, odebrane[str(key)]['text'][:30] + i, 25).display()
                        ky = ky + 50
            elif route == '124':   # wyswietlnanie wyslanych smsow
                ky = 0
                for key in range(wyslane["number"], 0, -1):
                    if isinstance(wyslane[str(key)], int) == False and float(key)<=wyslane['number']-(wyslane_strona*8) and float(key)>(wyslane['number']-(wyslane_strona*8))-8:
                        if len(wyslane[str(key)]['text']) > 30: i = '...' 
                        else: i = ''
                        notFound = True
                        for key2 in kontakty:
                            if isinstance(kontakty[key2], int) == False and kontakty[key2]['tel'][-9:] == wyslane[str(key)]['tel'][-9:]:
                                KeyboardInput(0,ky, kontakty[key2]['text'], False, 320,50,center_szerokosc(kontakty[key2]['text'],25),7,25).display()
                                notFound = False
                        if notFound: KeyboardInput(0,ky, wyslane[str(key)]['tel'][-9:], False, 320,50,center_szerokosc(wyslane[str(key)]['tel'][-9:],25),7,25).display()
                        Text(center_szerokosc(wyslane[str(key)]['text'][:30] + i, 25), ky+28, wyslane[str(key)]['text'][:30] + i, 25).display()
                        ky = ky + 50
        elif route[:4] == '1231' or route[:4] == '1241':   # wyswietlanie szczegolow smsow ODEBRANE/WYSLANE
            numer = route[4:]
            tresc = odebrane[numer]['text'] if route[:4] == '1231' else wyslane[numer]['text']
            linieTab = []
            for x in range(0, len(tresc)):
                if pygame.font.Font(None,30).size(tresc[:x])[0] >= 250:
                    linieTab.append(tresc[:x])
                    tresc = tresc[x:]
            linieTab.append(tresc)
            ky = 20
            for item in linieTab:
                Text(10,ky,item, 30).display()
                ky = ky + 30
            Text(center_szerokosc('POWRÓT', 20),450,'POWRÓT', 20).display()
        elif route[:4] == '1141':                   # Okno potwierdzenia usuwania kontaktow
            numer = route[4:]
            Text(center_szerokosc('CZY NAPEWNO CHCESZ USUNĄĆ KONTAKT?', 20),150,'CZY NAPEWNO CHCESZ USUNĄĆ KONTAKT?', 20).display()
            Text(center_szerokosc(kontakty[numer]['text'], 40),200,kontakty[numer]['text'], 40).display()
            Text(center_szerokosc(kontakty[numer]['tel'], 40),240, kontakty[numer]['tel'], 40).display()
            Circle(80, 375, 50).display()
            Circle(240, 375, 50).display()
            Text(center_szerokosc('TAK', 40) - 80, 365, 'TAK', 40).display()
            Text(center_szerokosc('NIE', 40) + 80, 365, 'NIE', 40).display()

    #~~~~~~~~~~~~~~~~~~RENDEROWANIE KLAWIATURY~~~~~~~~~~~~~~~~~~

        if keyboard[0]:                        # Renderowanie klawiatury QWERTY
            kx = 0
            ky = 280
            for letter in keyboardArray[0]:
                KeyboardInput(kx,ky, letter, keyboard_upper).display()
                kx = kx + 32
                if kx == 320:
                    kx = 0
                    ky = ky + 40
            KeyboardInput(0, ky, 'SHIFT', keyboard_upper).display()
            KeyboardInput(60, ky, 'SPACJA', keyboard_upper).display()
            if route == '1131':
                KeyboardInput(130, ky, 'DODAJ', keyboard_upper).display()
            else:
                KeyboardInput(130, ky, 'WYŚLIJ', keyboard_upper).display()
            KeyboardInput(200, ky, 'USUŃ', keyboard_upper).display()
            KeyboardInput(260, ky, 'WRÓĆ', keyboard_upper).display()

        elif keyboard[1]:                       # Renderowanie klawiatury numerycznej
            kx = 0
            ky = 200
            for number in keyboardArray[1]:
                KeyboardInput(kx, ky, number, False, 80, 80, 30, 25, 50).display()
                kx = kx + 80
                if kx == 320:
                    kx = 0
                    ky = ky + 80
            KeyboardInput(0, ky, 'POPRAW', False, 100, 40, 5, 10, 30).display()
            KeyboardInput(100, ky, 'WYBIERZ', False, 220, 40, 15, 10, 30).display()
            KeyboardInput(220, ky, 'POWRÓT', False, 320, 40, 5, 10, 30).display()

    #-------------------------------------------------------------------------------------------
    #
    #               IMPLEMENTACJA PETLI SPRAWDZAJACEJ NOWE POLACZENIA + SMSY
    #               
    #         Trzeba dodatkowo zakodowac interfejs przychodzacych polaczen i nowych smsow
    #         Zapis nowych smsów do odebrane.txt
    #
    #-------------------------------------------------------------------------------------------

#~~~~~~~~~~~~~~~~~~UPDATE EKRANU~~~~~~~~~~~~~~~~~~
        pygame.display.update()                 # wyswietl wyrenderowane elementy
pygame.quit()
