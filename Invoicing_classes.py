import sys, re
import PyQt5
from PyQt5.QtWidgets import QApplication, QLineEdit, QMainWindow, QMessageBox, QDialog, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView, QSpinBox, QDoubleSpinBox, QGraphicsView, QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, QDate, Qt
from PyQt5.QtGui import QIcon, QPixmap, QFont, QImage

import shutil, os
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader #For logo

import matplotlib.pyplot as plt
import numpy as np
import datetime

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import urllib.request

import sqlite3
import os.path

now = datetime.datetime.now()

day = now.day
month = now.month
year = now.year

current_datetime = '%s/%s/%s' % (day, month, year)

mesos = ['Gener', 'Febrer', 'Març', 'Abril', 'Maig', 'Juny', 'Juliol', 'Agost', 'Setembre', 'Octubre', 'Novembre', 'Desembre']
mesos_minus = ['gener', 'febrer', 'març', 'abril', 'maig', 'juny', 'juliol', 'agost', 'setembre', 'octubre', 'novembre', 'desembre']

clear = lambda: os.system('cls')

dir_principal = os.getcwd()
carpeta_data = dir_principal + '\Data'
carpeta_factures = dir_principal + '\Factures'
carpeta_abonos = dir_principal + '\Abonos'
carpeta_albaranes = dir_principal + '\Albaranes'
current_month_factures = carpeta_factures + '\%s_%s' % (mesos[int(month)-1], year)

if not os.path.exists(carpeta_data): os.makedirs(carpeta_data)
if not os.path.exists(carpeta_factures): os.makedirs(carpeta_factures)
if not os.path.exists(carpeta_abonos): os.makedirs(carpeta_abonos)

#####################################################################
#																	#
#							FUNCTIONS								#
#																	#
#####################################################################

#DRIVE
def fitxer_drive(name):
	
	count = False

	file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

	for file1 in file_list:
		if file1['title'] == name:
			file = drive.CreateFile({'id': file1['id']})
			count = True

	if count == False:
		file = drive.CreateFile({'title': name})

	file.SetContentFile(name)
	file.Upload()

def carpeta_drive(folder_name):
	
	count = False

	file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

	for file1 in file_list:
		if file1['title'] == folder_name: #La carpeta ja està creada
			Factures_id = file1['id'] 
			count = True

	if count == False: #Crear la carpeta
		# Create folder. 
		folder_metadata = {
	    'title' : folder_name,
	    # The mimetype defines this new file as a folder, so don't change this.
	    'mimeType' : 'application/vnd.google-apps.folder'
		}

		folder = drive.CreateFile(folder_metadata)
		folder.Upload()
		
		file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

		for file1 in file_list:
			if file1['title'] == folder_name: 
				Factures_id = file1['id'] 

	return Factures_id

def file_to_folder(folder_id, filename):

	file = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": folder_id}]})

	file.SetContentFile(filename)

	file.Upload()

def delete_file_in_folder(folder_id, filename):
	file_list = drive.ListFile({'q': "'%s' in parents and trashed=false" % folder_id}).GetList()

	for file1 in file_list:
		if file1['title'] == filename: #L'arxiu ja està creat
			file1.Delete()

def internet_on():
    try:
        urllib.request.urlopen('http://216.58.192.142', timeout=1)
        return True
    except urllib.request.URLError as err:
    	return False

def upload_to_drive_database(name):
	global drive

	os.chdir(carpeta_data)

	##################################### LOG IN GOOGLE DRIVE #############################################
	int_connexion = internet_on()

	if int_connexion == True:

		gauth = GoogleAuth()
		gauth.LocalWebserverAuth() 

		drive = GoogleDrive(gauth)

	########################################################################################################

	#Pujar base de dades clients

	if int_connexion == True:
		folder_id = carpeta_drive('Data') #Pujar a google drive la factura
		filename = '%s.db' % name

		delete_file_in_folder(folder_id,filename)
		file_to_folder(folder_id, filename)

def upload_to_drive_factura(dirr, NAME, NAME_2, num_fact, data, NOMCOM, num_client, filename_ventes, filename_facturacio_clients, filename_facturacio_total, filename_factures_emeses):

	global drive

	mes = mesos[int(data[3:5])-1]
	ano = str(data[6:]).zfill(4)

	current_month_factures = dirr + '\%s_%s' % (mes, ano)

	##################################### LOG IN GOOGLE DRIVE #############################################
	int_connexion = internet_on()

	if int_connexion == True:
		previous_directory = os.getcwd()
		os.chdir(carpeta_data)

		gauth = GoogleAuth()
		gauth.LocalWebserverAuth() 

		drive = GoogleDrive(gauth)

		os.chdir(previous_directory)
	########################################################################################################

	#Guardar la factura al drive
	os.chdir(current_month_factures)

	if int_connexion == True:
		folder_id = carpeta_drive('%s_%s_%s' % (NAME, mes, str(year))) #Pujar a google drive la factura
		filename = '%s_%s_%s_%s.pdf' % (NAME_2, str(num_fact).zfill(4), NOMCOM, str(num_client).zfill(4))

		delete_file_in_folder(folder_id,filename)
		file_to_folder(folder_id, filename)

		folder_id = carpeta_drive('Data') #Pujar bases de dades

		os.chdir(carpeta_data)

		#Ventes
		delete_file_in_folder(folder_id,filename_ventes)
		file_to_folder(folder_id, filename_ventes)

		#Facturació clients
		delete_file_in_folder(folder_id,filename_facturacio_clients)
		file_to_folder(folder_id, filename_facturacio_clients)

		#Facturació total
		delete_file_in_folder(folder_id,filename_facturacio_total)
		file_to_folder(folder_id, filename_facturacio_total)

		#Factures emeses
		delete_file_in_folder(folder_id,filename_factures_emeses)
		file_to_folder(folder_id, filename_factures_emeses)


#FACTURES
def assignar_numero_factura(table, year):
	tablas = [
				"""
					CREATE TABLE IF NOT EXISTS numero_factura(
						any TEXT NOT NULL,
						num TEXT NOT NULL
					); 
				""" 
			]

	create_database('CompanyName', tablas)

	tablas = [
				"""
					CREATE TABLE IF NOT EXISTS numero_abono(
						any TEXT NOT NULL,
						num TEXT NOT NULL
					); 
				""" 
			]

	create_database('CompanyName', tablas)

	tablas = [
				"""
					CREATE TABLE IF NOT EXISTS numero_albaran(
						any TEXT NOT NULL,
						num TEXT NOT NULL
					); 
				""" 
			]

	create_database('CompanyName', tablas)

	database = sqlite3.connect('CompanyName.db')
	cursor = database.cursor()

	sentencia = "SELECT * FROM %s WHERE any LIKE %s" % (table, year)

	cursor.execute(sentencia)
	lines = cursor.fetchall()

	if len(lines) == 0:
		sentencia = "INSERT INTO '%s'(any, num) VALUES (?,?)" % (table)
		cursor.execute(sentencia, [year, 1])
		database.commit()

		return 1

	else:
		num_fact = int(lines[0][1]) + 1

		sentencia = "DELETE FROM '%s' WHERE any LIKE ?;" % table
		cursor.execute(sentencia, [ "%{}%".format(year)])
		database.commit()

		sentencia = "INSERT INTO '%s'(any, num) VALUES (?,?)" % (table)
		cursor.execute(sentencia, [year, num_fact])
		database.commit()

		return num_fact

def factura(dirr, NAME, num_client, NOMCOM, NOMFIS, DIR, NIF, TEL, POBLACIO, num_fact, date, form_pag, dim, array_ref, array_concept, array_U, array_PU, array_BI, SUMA, IVA, TOTAL):
	global c

	CompanyName = 'COMPANY NAME'
	CompanyDirection = 'C/ street, nº fºfª'
	PC = 'CP'
	CITY = 'CITY'
	EMAIL = 'companyemail'


	FISCAL_NAME = 'Fiscal Name'
	ID = 'ID_number'
	FISCAL_DIRECTION = 'Fiscal direction'
	FISCAL_CITY = 'Fiscal city'
	FISCAL_PC = 'Fiscal P.C.'

	mes = mesos[int(date[3:5])-1]
	ano = str(date[6:]).zfill(4)

	current_month_factures = dirr + '\%s_%s' % (mes, ano)

	if not os.path.exists(current_month_factures): os.makedirs(current_month_factures)

	os.chdir(current_month_factures)

	c = canvas.Canvas("%s_%s_%s_%s.pdf" % (NAME, str(num_fact).zfill(4), NOMCOM, str(num_client).zfill(4)))

	x_CompanyName = 40
	x_customer = 350
	x_doc = 350

	y_CompanyName = 690
	y_customer = 810
	y_doc = 680

	y_title = 780

	c.setFont('Helvetica', 20)

	#Title (may be substituted by a logo)
	logo = ImageReader(carpeta_data + '\logo.png')
	c.drawImage(logo, x_CompanyName + 50, y_CompanyName + 50, width=50, height=50, mask='auto')

	c.setFont('Helvetica', 10)

	#CompanyName data
	c.drawString(x_CompanyName, y_CompanyName, CompanyName)
	c.drawString(x_CompanyName, y_CompanyName - 15, CompanyDirection)
	c.drawString(x_CompanyName, y_CompanyName - 15*2, PC + '' + CITY)
	c.drawString(x_CompanyName, y_CompanyName - 15*3, 'EMAIL: %s' % EMAIL)
	#c.drawString(x_CompanyName, y_CompanyName - 15*4, 'TELF: 640087843-678230059')

	#Customer data
	c.drawString(x_customer, y_customer, 'CUSTOMER')
	c.line(x_customer, y_customer - 5, x_customer + 35, y_customer - 5)
	c.drawString(x_customer, y_customer - 5 - 15, str(num_client).zfill(4) + ' ' + NOMCOM)
	c.drawString(x_customer, y_customer - 5 - 15*2, NOMFIS)
	c.drawString(x_customer, y_customer - 5 - 15*3, DIR)
	c.drawString(x_customer, y_customer - 5 - 15*4, POBLACIO)
	c.drawString(x_customer, y_customer - 5 - 15*5, 'NIF: ' + NIF)
	c.drawString(x_customer, y_customer - 5 -15*6, 'TEL: ' + TEL)

	#Document data
	c.drawString(x_doc, y_doc, 'DOCUMENT')
	c.line(x_doc, y_doc-5, x_doc + 60, y_doc-5)
	c.drawString(x_doc, y_doc-5-15*1, '%s: ' % NAME + str(num_fact).zfill(4))
	c.drawString(x_doc, y_doc-5-15*2, 'DATE: ' + date)
	c.drawString(x_doc, y_doc-5-15*3, 'WAY TO PAY: ' + form_pag)

	#Make the table

	x_ref = 50
	x_concepte = 90
	x_U = 400
	x_PU = 450
	x_BI = 500

	y_ref = 580
	y_concepte = 580
	y_U = 580
	y_PU = 580
	y_BI = 580

	x_final_tabla = 550
	y_final_tabla = 200

	c.drawString(x_ref, y_ref, 'REF')
	c.drawString(x_concepte+5, y_concepte, 'CONCEPT')
	c.drawString(x_U+5, y_U, 'Units')
	c.drawString(x_PU+10, y_PU, 'U.P.')
	c.drawString(x_BI + 5, y_BI, 'T.B.')
	c.line(x_ref-10, y_ref-5, x_final_tabla, y_BI-5) #linea sota el encabezado
	c.line(x_ref-10, y_ref-5, x_ref-10, y_final_tabla) #linea vertical inicial
	c.line(x_concepte-10, y_ref-5, x_concepte-10, y_final_tabla) #linea vertical despres de ref
	c.line(x_U-3, y_U-5, x_U-3, y_final_tabla) #linea vertical dsps de concepte
	c.line(x_PU-5, y_PU-5, x_PU-5, y_final_tabla) #linea dsps de unitats
	c.line(x_BI-7, y_BI-5, x_BI-7, y_final_tabla) #linea vertical dsps de P.U.
	c.line(x_final_tabla, y_ref-5, x_final_tabla, y_final_tabla) #ultima linea vertical

	#c.line(x_ref-10, y_final_tabla+20, x_final_tabla, y_final_tabla+20) #penultima linea horitzontal
	c.line(x_ref-10, y_final_tabla, x_final_tabla, y_final_tabla ) #ultima linea horitzontal

	# Taula de resultats finals

	x_0 = x_ref-10
	y_0 = y_final_tabla - 30

	x_f = x_final_tabla
	y_f = y_0 - 25

	c.line(x_0, y_0, x_f, y_0) #primera linea horitzontal
	c.line(x_0, y_f, x_f, y_f) #ultima linea horitzontal

	x_1 = (x_f-x_0)/3 
	x_2 = 2*x_1

	c.line(x_0, y_0, x_0, y_f) #linia vertical inicial
	c.line(x_1,y_0, x_1, y_f) #primera linea vertical
	c.line(x_2,y_0,x_2,y_f) #ultima linea vertical
	c.line(x_f,y_0,x_f,y_f) #linea vertical final
	
	#Introduir referencies, conceptes, unitats, preu unitats, base imponible, suma total, iva i suma final

	y_new = y_ref-20
	sep = 15

	for i in range(0, dim):
		c.drawString(x_ref, y_new -sep*i, array_ref[i])
		c.drawString(x_concepte + 5, y_new -sep*i, array_concept[i])
		c.drawString(x_U + 15, y_new -sep*i, str(array_U[i]))
		c.drawString(x_PU + 5, y_new -sep*i, str(array_PU[i]))
		c.drawString(x_BI + 5, y_new -sep*i, str(array_BI[i]))

	#c.drawString(x_BI + 5, y_final_tabla + 7, str(SUMA))	

	c.drawString(x_0 + 20, y_0-15, 'T.B.: ' + str(SUMA))
	c.drawString(x_1 + 50, y_0 - 15, 'V.A.T. 21%: ' + str(IVA))
	c.setFont('Helvetica-Bold', 10)
	c.drawString(x_2 + 50, y_0 - 15, 'TOTAL: ' + str(TOTAL) + '\u20ac')

	x_dades_personals = x_0
	y_dades_personals = y_f - 100

	c.setFont('Helvetica', 8)
	c.drawString(x_dades_personals, y_dades_personals, '%s, %s, %s, %s, %s' % (FISCAL_NAME, ID, FISCAL_DIRECTION, FISCAL_PC, FISCAL_CITY))

	c.save()

def factura_de_albaranes(dirr, NAME, num_client, NOMCOM, NOMFIS, DIR, NIF, TEL, POBLACIO, num_fact, date, form_pag, array_num, array_data, array_bi, array_iva, array_total, SUMA, IVA, TOTAL):
	global c

	CompanyName = 'COMPANY NAME'
	CompanyDirection = 'C/ street, nº fºfª'
	PC = 'CP'
	CITY = 'CITY'
	EMAIL = 'companyemail'


	FISCAL_NAME = 'Fiscal Name'
	ID = 'ID_number'
	FISCAL_DIRECTION = 'Fiscal direction'
	FISCAL_CITY = 'Fiscal city'
	FISCAL_PC = 'Fiscal P.C.'

	mes = mesos[int(date[3:5])-1]
	ano = str(date[6:]).zfill(4)

	current_month_factures = dirr + '\%s_%s' % (mes, ano)

	if not os.path.exists(current_month_factures): os.makedirs(current_month_factures)

	os.chdir(current_month_factures)

	c = canvas.Canvas("%s_%s_%s_%s.pdf" % (NAME, str(num_fact).zfill(4), NOMCOM, str(num_client).zfill(4)))

	x_CompanyName = 40
	x_customer = 350
	x_doc = 350

	y_CompanyName = 690
	y_customer = 810
	y_doc = 680

	y_title = 780

	c.setFont('Helvetica', 20)

	#Title (may be substituted by a logo)
	logo = ImageReader(carpeta_data + '\logo.png')
	c.drawImage(logo, x_amilcar + 50, y_amilcar + 50, width=50, height=50, mask='auto')

	c.setFont('Helvetica', 10)

	#CompanyName data
	c.drawString(x_CompanyName, y_CompanyName, CompanyName)
	c.drawString(x_CompanyName, y_CompanyName - 15, CompanyDirection)
	c.drawString(x_CompanyName, y_CompanyName - 15*2, PC + '' + CITY)
	c.drawString(x_CompanyName, y_CompanyName - 15*3, 'EMAIL: %s' % EMAIL)
	#c.drawString(x_CompanyName, y_CompanyName - 15*4, 'TELF: 640087843-678230059')

	#Customer data
	c.drawString(x_customer, y_customer, 'CUSTOMER')
	c.line(x_customer, y_customer - 5, x_customer + 35, y_customer - 5)
	c.drawString(x_customer, y_customer - 5 - 15, str(num_client).zfill(4) + ' ' + NOMCOM)
	c.drawString(x_customer, y_customer - 5 - 15*2, NOMFIS)
	c.drawString(x_customer, y_customer - 5 - 15*3, DIR)
	c.drawString(x_customer, y_customer - 5 - 15*4, POBLACIO)
	c.drawString(x_customer, y_customer - 5 - 15*5, 'NIF: ' + NIF)
	c.drawString(x_customer, y_customer - 5 -15*6, 'TEL: ' + TEL)

	#Document data
	c.drawString(x_doc, y_doc, 'DOCUMENT')
	c.line(x_doc, y_doc-5, x_doc + 60, y_doc-5)
	c.drawString(x_doc, y_doc-5-15*1, '%s: ' % NAME + str(num_fact).zfill(4))
	c.drawString(x_doc, y_doc-5-15*2, 'DATE: ' + date)
	c.drawString(x_doc, y_doc-5-15*3, 'WAY TO PAY: ' + form_pag)

	#Make the table

	x_ref = 50
	x_concepte = 90
	x_U = 400
	x_PU = 450
	x_BI = 500

	y_ref = 580
	y_concepte = 580
	y_U = 580
	y_PU = 580
	y_BI = 580

	x_final_tabla = 550
	y_final_tabla = 200

	c.drawString(x_ref, y_ref, 'Nº')
	c.drawString(x_concepte+5, y_concepte, 'DATE')
	c.drawString(x_U+5, y_U, 'T.B.')
	c.drawString(x_PU+10, y_PU, 'V.A.T.')
	c.drawString(x_BI + 5, y_BI, 'TOTAL')
	c.line(x_ref-10, y_ref-5, x_final_tabla, y_BI-5) #linea sota el encabezado
	c.line(x_ref-10, y_ref-5, x_ref-10, y_final_tabla) #linea vertical inicial
	c.line(x_concepte-10, y_ref-5, x_concepte-10, y_final_tabla) #linea vertical despres de ref
	c.line(x_U-3, y_U-5, x_U-3, y_final_tabla) #linea vertical dsps de concepte
	c.line(x_PU-5, y_PU-5, x_PU-5, y_final_tabla) #linea dsps de unitats
	c.line(x_BI-7, y_BI-5, x_BI-7, y_final_tabla) #linea vertical dsps de P.U.
	c.line(x_final_tabla, y_ref-5, x_final_tabla, y_final_tabla) #ultima linea vertical

	#c.line(x_ref-10, y_final_tabla+20, x_final_tabla, y_final_tabla+20) #penultima linea horitzontal
	c.line(x_ref-10, y_final_tabla, x_final_tabla, y_final_tabla ) #ultima linea horitzontal

	# Taula de resultats finals

	x_0 = x_ref-10
	y_0 = y_final_tabla - 30

	x_f = x_final_tabla
	y_f = y_0 - 25

	c.line(x_0, y_0, x_f, y_0) #primera linea horitzontal
	c.line(x_0, y_f, x_f, y_f) #ultima linea horitzontal

	x_1 = (x_f-x_0)/3 
	x_2 = 2*x_1

	c.line(x_0, y_0, x_0, y_f) #linia vertical inicial
	c.line(x_1,y_0, x_1, y_f) #primera linea vertical
	c.line(x_2,y_0,x_2,y_f) #ultima linea vertical
	c.line(x_f,y_0,x_f,y_f) #linea vertical final
	
	#Introduir referencies, conceptes, unitats, preu unitats, base imponible, suma total, iva i suma final

	y_new = y_ref-20
	sep = 15

	for i in range(len(array_bi)):
		c.drawString(x_ref, y_new -sep*i, array_num[i])
		c.drawString(x_concepte + 5, y_new -sep*i, array_data[i])
		c.drawString(x_U + 15, y_new -sep*i, str(array_bi[i]))
		c.drawString(x_PU + 5, y_new -sep*i, str(array_iva[i]))
		c.drawString(x_BI + 5, y_new -sep*i, str(array_total[i]))

	#c.drawString(x_BI + 5, y_final_tabla + 7, str(SUMA))	

	c.drawString(x_0 + 20, y_0-15, 'TOTAL T.B..: ' + str(SUMA))
	c.drawString(x_1 + 50, y_0 - 15, 'TOTAL V.A.T.: ' + str(IVA))
	c.setFont('Helvetica-Bold', 10)
	c.drawString(x_2 + 50, y_0 - 15, 'FINAL TOTAL: ' + str(TOTAL) + '\u20ac')

	x_dades_personals = x_0
	y_dades_personals = y_f - 100

	c.setFont('Helvetica', 8)
	c.drawString(x_dades_personals, y_dades_personals, '%s, %s, %s, %s, %s' % (FISCAL_NAME, ID, FISCAL_DIRECTION, FISCAL_PC, FISCAL_CITY))
	

	c.save()


#BASEES DE DADES
def create_database_client(name):
		#Create a database
		database = sqlite3.connect("%s.db" % name)

		#Create a data table in the database
		cursor = database.cursor()
		tablas = [
				"""
					CREATE TABLE IF NOT EXISTS data(
						num_client TEXT NOT NULL,
						nom_comercial TEXT NOT NULL,
						nom_fiscal TEXT NOT NULL,
						adreça TEXT NOT NULL,
						poblacio TEXT NOT NULL,
						nif TEXT NOT NULL,
						telf TEXT NOT NULL,
						forma_pago TEXT NOT NULL
					);
				"""
			]
		for tabla in tablas:
			cursor.execute(tabla);

def fill_database(name, numclient, nomcom, nomfis, adreça, poblacio, nif, telf, formapago):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	sentencia = "INSERT INTO data(num_client, nom_comercial, nom_fiscal, adreça, poblacio, nif, telf, forma_pago) VALUES (?,?,?,?,?,?,?,?)"
	cursor.execute(sentencia, [numclient, nomcom, nomfis, adreça, poblacio, nif, telf, formapago])

	database.commit()

def read_database(name, table, name_2, order):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()
	sentencia = "SELECT * FROM '%s' ORDER BY %s %s;" % (table, name_2, order)
 
	cursor.execute(sentencia)
	
	lines = cursor.fetchall()

	cursor.close()
	
	return lines

def select_from_database(name, busqueda, name_2):
	os.chdir(carpeta_data)

	database = sqlite3.connect('%s.db' % name)
	cursor=database.cursor()

	sentencia = "SELECT * FROM data WHERE nom_comercial LIKE ? ORDER BY %s ASC;" % name_2

	cursor.execute(sentencia, [ "%{}%".format(busqueda)])

	matches = cursor.fetchall()

	if len(matches) != 0:
		return matches, True

	else:
		sentencia = "SELECT * FROM data WHERE num_client LIKE ?;"

		cursor.execute(sentencia, [ "%{}%".format(busqueda)])

		matches = cursor.fetchall()

		if len(matches) != 0:
			return matches, True

		else:
			return matches, False

def select_from_database_general(name, table, busqueda, name_2, order, order_2):
	os.chdir(carpeta_data)

	database = sqlite3.connect('%s.db' % name)
	cursor=database.cursor()

	sentencia = "SELECT * FROM '%s' WHERE %s LIKE ? ORDER BY %s %s;" % (table, name_2, order, order_2)

	cursor.execute(sentencia, ["%{}%".format(busqueda)])

	matches = cursor.fetchall()

	return matches

def delete_from_database(name, name_2, num):
	os.chdir(carpeta_data)

	database = sqlite3.connect('%s.db' % name)
	cursor=database.cursor()

	sentencia = "DELETE FROM data WHERE %s LIKE ?;" % name_2

	cursor.execute(sentencia, [ "%{}%".format(num)])

	database.commit()

def delete_from_database_general(name, table, name_2, num):
	os.chdir(carpeta_data)

	database = sqlite3.connect('%s.db' % name)
	cursor=database.cursor()

	sentencia = "DELETE FROM '%s' WHERE %s LIKE ?;" % (table, name_2)

	cursor.execute(sentencia, [ "%{}%".format(num)])

	database.commit()

def create_database_ventes(name, table):
	database = sqlite3.connect("%s.db" % name)

	cursor = database.cursor()
	tablas = [
			"""
				CREATE TABLE IF NOT EXISTS '%s'(
					ref TEXT NOT NULL,
					gener REAL NOT NULL,
					febrer REAL NOT NULL,
					març REAL NOT NULL,
					abril REAL NOT NULL,
					maig REAL NOT NULL,
					juny REAL NOT NULL,
					juliol REAL NOT NULL,
					agost REAL NOT NULL,
					setembre REAL NOT NULL,
					octubre REAL NOT NULL,
					novembre REAL NOT NULL,
					desembre REAL NOT NULL
				);
			""" % table
		]
	for tabla in tablas:
		cursor.execute(tabla);

def create_database_cataleg(name):
	#Create a database
	database = sqlite3.connect("%s.db" % name)

	#Create a data table in the database
	cursor = database.cursor()
	tablas = [
			"""
				CREATE TABLE IF NOT EXISTS data(
					ref TEXT NOT NULL,
					prod TEXT NOT NULL,
					preu REAL NOT NULL
				);
			"""
		]
	for tabla in tablas:
		cursor.execute(tabla);

def fill_database_cataleg(name, ref, prod, preu):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	sentencia = "INSERT INTO data(ref, prod, preu) VALUES (?,?,?)"
	cursor.execute(sentencia, [ref, prod, preu])

	database.commit()

def fill_database_ventes(name, tabla, ref, month, ventes, zfill_ref):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	llista = [str(ref).zfill(zfill_ref), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

	#Tenir en compte les unitats venudes prèviament
	sentencia = "SELECT * FROM '%s' WHERE ref LIKE ?;" % tabla
	cursor.execute(sentencia, ["%{}%".format(ref)])

	matches = cursor.fetchall()

	if len(matches) != 0:

		llista = []
		for i in range(len(matches[0])):
			llista.append(matches[0][i])

		nou = llista[month] + ventes

		llista[month] = nou

		#Eliminar la fila actual 
		sentencia = "DELETE FROM '%s' WHERE ref LIKE ?;" % tabla

		cursor.execute(sentencia, [ "%{}%".format(ref)])

		#Escriure les ventes actualitzades
		sentencia = "INSERT INTO '%s'(ref, gener, febrer, març, abril, maig, juny, juliol, agost, setembre, octubre, novembre, desembre) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)" % tabla
		cursor.execute(sentencia, llista)

	else:
		#Escriure les ventes actualitzades
		llista[month] = ventes
		sentencia = "INSERT INTO '%s'(ref, gener, febrer, març, abril, maig, juny, juliol, agost, setembre, octubre, novembre, desembre) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)" % tabla
		cursor.execute(sentencia, llista)


	database.commit()

def create_database_preus(name):
	database = sqlite3.connect("%s.db" % name)
	cursor = database.cursor()

	tablas = [
			"""
				CREATE TABLE IF NOT EXISTS data(
					num_client TEXT NOT NULL,
					ref TEXT NOT NULL,
					preu REAL NOT NULL
				);
			"""
		]
	for tabla in tablas:
		cursor.execute(tabla);

def fill_database_preus(name, num, ref, prod, preu):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	lines = select_from_database_preus(name, num, ref)

	if len(lines) != 0:
		return False
	else:
		sentencia = "INSERT INTO data(num_client, ref, prod, preu) VALUES (?,?,?,?)"
		cursor.execute(sentencia, [num, ref, prod, preu])
		database.commit()
		return True

def modificar_database_preus(name, num, ref, prod, preu):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	lines = select_from_database_preus(name, num, ref)

	if len(lines) == 0:
		return False

	else:
		sentencia = "DELETE FROM data WHERE num_client LIKE ? AND ref LIKE ?;"
		cursor.execute(sentencia, [ "%{}%".format(num), "%{}%".format(ref)])

		sentencia = "INSERT INTO data(num_client, ref, prod, preu) VALUES (?,?,?,?)"
		cursor.execute(sentencia, [num, ref, prod, preu])
		database.commit()

		return True

def select_from_database_preus(name, num, ref):
	database = sqlite3.connect('%s.db' % name)
	cursor=database.cursor()

	sentencia = "SELECT * FROM data WHERE num_client LIKE ? AND ref LIKE ?;" 

	cursor.execute(sentencia, ["%{}%".format(num), "%{}%".format(ref)])

	matches = cursor.fetchall()

	return matches

def create_database_factures(name):
	#Create a database
	database = sqlite3.connect("%s.db" % name)

	#Create a data table in the database
	cursor = database.cursor()
	tablas = [
			"""
				CREATE TABLE IF NOT EXISTS data(
					dia TEXT NOT NULL,
					mes TEXT NOT NULL,
					any TEXT NOT NULL,
					nom TEXT NOT NULL,
					base_imp REAL NOT NULL,
					iva REAL NOT NULL,
					total REAL NOT NULL
				);
			"""
		]
	for tabla in tablas:
		cursor.execute(tabla);

def fill_database_factures(name, dia, mes, any, nom, base, iva, total):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	sentencia = "INSERT INTO data(dia, mes, any, nom, base_imp, iva, total) VALUES (?,?,?,?,?,?,?)"
	cursor.execute(sentencia, [dia, mes, any, nom, base, iva, total])

	database.commit()

def delete_database_factures(name, dia, mes, any, base, iva, total):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	sentencia = "DELETE FROM data WHERE dia LIKE ? AND mes LIKE ? AND any LIKE ? AND base_imp LIKE ? AND iva LIKE ? AND total LIKE ? ;"
	cursor.execute(sentencia, [ "%{}%".format(dia), "%{}%".format(mes), "%{}%".format(any), "%{}%".format(base), "%{}%".format(iva), "%{}%".format(total)])

	database.commit()

def read_database_factures(name, order):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()
	sentencia = "SELECT * FROM data ORDER BY any, mes, dia %s" %  order
 
	cursor.execute(sentencia)
	
	lines = cursor.fetchall()
	
	return lines

def select_from_database_factures(name, dia, mes, ano):

	database = sqlite3.connect('%s.db' % name)
	cursor=database.cursor()

	sentencia = "SELECT * FROM data WHERE dia LIKE ? AND mes LIKE ? AND any LIKE ? ;" 
	cursor.execute(sentencia, ["%{}%".format(dia), "%{}%".format(mes), "%{}%".format(ano)])

	matches = cursor.fetchall()

	return matches

def check_table_exists(name, table):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	sentencia = "SELECT name FROM sqlite_master WHERE type='table' AND name = '%s' ;" % table
	cursor.execute(sentencia)

	lines = cursor.fetchall()

	if len(lines) == 0:
		return False
	else:
		return True

def create_database(name, tablas):
	#Create a database
	database = sqlite3.connect("%s.db" % name)

	#Create a data table in the database
	cursor = database.cursor()
	
	for tabla in tablas:
		cursor.execute(tabla);

def fill_table_stock(name, items_list):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	sentencia = "DELETE FROM stock WHERE REF LIKE ?;"
	cursor.execute(sentencia, ["%{}%".format(items_list[0])])

	sentencia = "INSERT INTO stock(REF, NAME, QUANTITY, UNIT_PRICE, TOTAL_PRICE) VALUES (?,?,?,?,?)"
	cursor.execute(sentencia, items_list)

	database.commit()

def fill_database_general(name, table, interrogants, values):
	database = sqlite3.connect('%s.db' % name)
	cursor = database.cursor()

	sentencia = "INSERT INTO %s VALUES %s" % (table, interrogants) 
	cursor.execute(sentencia, values)
	database.commit()

#DATE
def change_date_format(date):
	return datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")


#####################################################################
#																	#
#							CLASSES									#
#																	#
#####################################################################

#CLIENTS
class Nou_client(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('NouClient.ui', self)
		os.chdir(dir_principal)

		self.nomcom.textChanged.connect(self.validar_nom_com) #Executa la funció validar_nom_com al clicar sobre el camp
		self.nomfis.textChanged.connect(self.validar_nom_fis)
		self.direccio.textChanged.connect(self.validar_direccio)
		self.poblacio.textChanged.connect(self.validar_poblacio)
		self.nif.textChanged.connect(self.validar_nif)
		self.telf.textChanged.connect(self.validar_telf)
		self.formapago.textChanged.connect(self.validar_forma_pago)
		self.accept_botton.clicked.connect(self.validar_dades)

		self.pujar_drive.clicked.connect(self.upload_database)

	def assignar_numero_client(self, name):
		database = sqlite3.connect('%s.db' % name)
		cursor = database.cursor()
		sentencia = "SELECT * FROM data;"
 
		cursor.execute(sentencia)
	
		clients = cursor.fetchall()

		num = len(clients) + 1

		return num

	def validar_nom_com(self):
		nom_com = self.nomcom.text()
		validar = re.match("^[a-z\sáéíóúàèìòùäëïöüñç0123456789'.-]+$", nom_com, re.I) #Permetre lletres a-z, espais, accents, numeros
		if nom_com == '': #Si esta buit bordes grocs							 #re.I ignora majuscules i minuscules			
			self.nomcom.setStyleSheet('border: 1px solid yellow;')
			return False, nom_com

		elif not validar:#Si no es valid bordes vermells
			self.nomcom.setStyleSheet('border: 1px solid red;')
			return False, nom_com

		else:
			self.nomcom.setStyleSheet('border: 1px solid green;')
			return True, nom_com

	def validar_nom_fis(self):
		nom_fis = self.nomfis.text()
		validar = re.match("^[a-z\sáéíóúàèìòùäëïöüñç0123456789'.-]+$", nom_fis, re.I) #Permetre lletres a-z, espais, accents, numeros
		if nom_fis == '': #Si esta buit bordes grocs							 #re.I ignora majuscules i minuscules			
			self.nomfis.setStyleSheet('border: 1px solid yellow;')
			return False, nom_fis

		elif not validar:#Si no es valid bordes vermells
			self.nomfis.setStyleSheet('border: 1px solid red;')
			return False, nom_fis

		else:
			self.nomfis.setStyleSheet('border: 1px solid green;')
			return True, nom_fis

	def validar_direccio(self):
		direccio = self.direccio.text()
		validar = re.match("^[a-z\sáéíóúàèìòùäëïöüñç0123456789'/,ªº.-]+$", direccio, re.I) #Permetre lletres a-z, espais, accents, numeros
		if direccio == '': #Si esta buit bordes grocs								
			self.direccio.setStyleSheet('border: 1px solid yellow;')
			return False, direccio

		elif not validar:#Si no es valid bordes vermells
			self.direccio.setStyleSheet('border: 1px solid red;')
			return False, direccio

		else:
			self.direccio.setStyleSheet('border: 1px solid green;')
			return True, direccio

	def validar_poblacio(self):
		poblacio = self.poblacio.text()
		validar = re.match("^[a-z\sáéíóúàèìòùäëïöüñç0123456789',.-]+$", poblacio, re.I) #Permetre lletres a-z, espais, accents, numeros
		if poblacio == '': #Si esta buit bordes grocs							 		
			self.poblacio.setStyleSheet('border: 1px solid yellow;')
			return False, poblacio

		elif not validar:#Si no es valid bordes vermells
			self.poblacio.setStyleSheet('border: 1px solid red;')
			return False, poblacio

		else:
			self.poblacio.setStyleSheet('border: 1px solid green;')
			return True, poblacio

	def validar_nif(self):
		nif = self.nif.text()
		validar = re.match('^[a-zñç0123456789]+$', nif, re.I) #Permetre lletres a-z, numeros
		if nif == '': #Si esta buit bordes grocs								
			self.nif.setStyleSheet('border: 1px solid yellow;')
			return False, nif

		elif not validar:#Si no es valid bordes vermells
			self.nif.setStyleSheet('border: 1px solid red;')
			return False, nif

		else:
			self.nif.setStyleSheet('border: 1px solid green;')
			return True, nif

	def validar_telf(self):
		telf = self.telf.text()
		validar = re.match('^[0123456789]+$', telf, re.I) #Permetre numeros
		if telf == '': #Si esta buit bordes grocs									
			self.nif.setStyleSheet('border: 1px solid yellow;')
			return False, telf

		elif not validar:#Si no es valid bordes vermells
			self.telf.setStyleSheet('border: 1px solid red;')
			return False, telf

		else:
			self.telf.setStyleSheet('border: 1px solid green;')
			return True, telf


	def validar_forma_pago(self):
		forma_pago = self.formapago.text()
		validar = re.match('^[a-zñç.-]+$', forma_pago, re.I) #Permetre lletres a-z #re.I ignora majuscules i minuscules
		if forma_pago == '': #Si esta buit bordes grocs							 			
			self.nif.setStyleSheet('border: 1px solid yellow;')
			return False, forma_pago

		elif not validar:#Si no es valid bordes vermells
			self.formapago.setStyleSheet('border: 1px solid red;')
			return False, forma_pago

		else:
			self.formapago.setStyleSheet('border: 1px solid green;')
			return True, forma_pago

	def validar_dades(self):

		bool_1, NOMCOM = self.validar_nom_com()
		bool_2, NOMFIS = self.validar_nom_fis()
		bool_3, DIR = self.validar_direccio()
		bool_4, POBLACIO = self.validar_poblacio()
		bool_5, NIF = self.validar_nif()
		bool_6, TEL = self.validar_telf()
		bool_7, forma_pago = self.validar_forma_pago()

		if bool_1 and bool_2 and bool_3 and bool_4 and bool_5 and bool_6 and bool_7:

			os.chdir(carpeta_data)

			create_database_client('clients') #Just if the database doesn't exist

			num_client = self.assignar_numero_client('clients')
			fill_database('clients', str(num_client).zfill(4), str(NOMCOM), str(NOMFIS), str(DIR), str(POBLACIO), str(NIF), str(TEL), str(forma_pago))

			if self.pujar_drive_check.isChecked():
				upload_to_drive_database('clients')

			QMessageBox.information(self, 'Dades correctes' , 'El client ha estat registrat a la base de dades amb número de client %s' % str(num_client).zfill(4), QMessageBox.Discard)

			self.reinit_dialog()

		else:
			QMessageBox.warning(self, 'Dades incorrectes' , 'Comprova que tots els camps estan omplerts correctament', QMessageBox.Discard)

	def upload_database(self):
		upload_to_drive_database('clients')
		QMessageBox.information(self, 'Information', 'Dades pujades correctament')

	def reinit_dialog(self):
		self.nomcom.setText('')
		self.nomfis.setText('')
		self.direccio.setText('')
		self.poblacio.setText('')
		self.nif.setText('')
		self.telf.setText('')
		self.formapago.setText('')

		self.nomcom.setStyleSheet('')
		self.nomfis.setStyleSheet('')
		self.direccio.setStyleSheet('')
		self.poblacio.setStyleSheet('')
		self.nif.setStyleSheet('')
		self.telf.setStyleSheet('')
		self.formapago.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
			self.pujar_drive_check.setChecked(True)
		else:
			event.ignore()

class Modificar_client(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('ModClient.ui', self)

		self.numclient.textChanged.connect(self.validar_num_client)
		self.searchbotton.clicked.connect(self.search)

		self.nomcom.textChanged.connect(self.validar_nom_com) #Executa la funció validar_nom_com al clicar sobre el camp
		self.nomfis.textChanged.connect(self.validar_nom_fis)
		self.direccio.textChanged.connect(self.validar_direccio)
		self.poblacio.textChanged.connect(self.validar_poblacio)
		self.nif.textChanged.connect(self.validar_nif)
		self.telf.textChanged.connect(self.validar_telf)
		self.formapago.textChanged.connect(self.validar_forma_pago)
		self.accept_botton.clicked.connect(self.validar_dades)

		self.pujar_drive.clicked.connect(self.upload_database)

	def search(self):

		os.chdir(carpeta_data)
		control, num = self.validar_num_client()

		if control == True:

			if os.path.exists('clients.db'):

				client = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')
				
				if len(client) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					self.reinit_dialog()
					
				else:
					self.nomcom.setText(client[0][1])
					self.nomfis.setText(client[0][2])
					self.direccio.setText(client[0][3])
					self.poblacio.setText(client[0][4])
					self.nif.setText(client[0][5])
					self.telf.setText(client[0][6])
					self.formapago.setText(client[0][7])

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client!')

		else:
			QMessageBox.warning(self, 'Warning', 'Número de client no vàlid!')

	def validar_num_client(self):

		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 

	def validar_nom_com(self):
		nom_com = self.nomcom.text()
		validar = re.match("^[a-z\sáéíóúàèìòùäëïöüñç0123456789'.-]+$", nom_com, re.I) #Permetre lletres a-z, espais, accents, numeros
		if nom_com == '': #Si esta buit bordes grocs							 #re.I ignora majuscules i minuscules			
			self.nomcom.setStyleSheet('border: 1px solid yellow;')
			return False, nom_com

		elif not validar:#Si no es valid bordes vermells
			self.nomcom.setStyleSheet('border: 1px solid red;')
			return False, nom_com

		else:
			self.nomcom.setStyleSheet('border: 1px solid green;')
			return True, nom_com

	def validar_nom_fis(self):
		nom_fis = self.nomfis.text()
		validar = re.match("^[a-z\sáéíóúàèìòùäëïöüñç0123456789'.-]+$", nom_fis, re.I) #Permetre lletres a-z, espais, accents, numeros
		if nom_fis == '': #Si esta buit bordes grocs							 #re.I ignora majuscules i minuscules			
			self.nomfis.setStyleSheet('border: 1px solid yellow;')
			return False, nom_fis

		elif not validar:#Si no es valid bordes vermells
			self.nomfis.setStyleSheet('border: 1px solid red;')
			return False, nom_fis

		else:
			self.nomfis.setStyleSheet('border: 1px solid green;')
			return True, nom_fis

	def validar_direccio(self):
		direccio = self.direccio.text()
		validar = re.match("^[a-z\sáéíóúàèìòùäëïöüñç0123456789'/,ªº.-]+$", direccio, re.I) #Permetre lletres a-z, espais, accents, numeros
		if direccio == '': #Si esta buit bordes grocs								
			self.direccio.setStyleSheet('border: 1px solid yellow;')
			return False, direccio

		elif not validar:#Si no es valid bordes vermells
			self.direccio.setStyleSheet('border: 1px solid red;')
			return False, direccio

		else:
			self.direccio.setStyleSheet('border: 1px solid green;')
			return True, direccio

	def validar_poblacio(self):
		poblacio = self.poblacio.text()
		validar = re.match("^[a-z\sáéíóúàèìòùäëïöüñç0123456789',.-]+$", poblacio, re.I) #Permetre lletres a-z, espais, accents, numeros
		if poblacio == '': #Si esta buit bordes grocs							 		
			self.poblacio.setStyleSheet('border: 1px solid yellow;')
			return False, poblacio

		elif not validar:#Si no es valid bordes vermells
			self.poblacio.setStyleSheet('border: 1px solid red;')
			return False, poblacio

		else:
			self.poblacio.setStyleSheet('border: 1px solid green;')
			return True, poblacio

	def validar_nif(self):
		nif = self.nif.text()
		validar = re.match('^[a-zñç0123456789]+$', nif, re.I) #Permetre lletres a-z, numeros
		if nif == '': #Si esta buit bordes grocs								
			self.nif.setStyleSheet('border: 1px solid yellow;')
			return False, nif

		elif not validar:#Si no es valid bordes vermells
			self.nif.setStyleSheet('border: 1px solid red;')
			return False, nif

		else:
			self.nif.setStyleSheet('border: 1px solid green;')
			return True, nif

	def validar_telf(self):
		telf = self.telf.text()
		validar = re.match('^[0123456789]+$', telf, re.I) #Permetre numeros
		if telf == '': #Si esta buit bordes grocs									
			self.nif.setStyleSheet('border: 1px solid yellow;')
			return False, telf

		elif not validar:#Si no es valid bordes vermells
			self.telf.setStyleSheet('border: 1px solid red;')
			return False, telf

		else:
			self.telf.setStyleSheet('border: 1px solid green;')
			return True, telf


	def validar_forma_pago(self):
		forma_pago = self.formapago.text()
		validar = re.match('^[a-zñç.]+$', forma_pago, re.I) #Permetre lletres a-z #re.I ignora majuscules i minuscules
		if forma_pago == '': #Si esta buit bordes grocs							 			
			self.nif.setStyleSheet('border: 1px solid yellow;')
			return False, forma_pago

		elif not validar:#Si no es valid bordes vermells
			self.formapago.setStyleSheet('border: 1px solid red;')
			return False, forma_pago

		else:
			self.formapago.setStyleSheet('border: 1px solid green;')
			return True, forma_pago

	def validar_dades(self):

		bool_1, NOMCOM = self.validar_nom_com()
		bool_2, NOMFIS = self.validar_nom_fis()
		bool_3, DIR = self.validar_direccio()
		bool_4, POBLACIO = self.validar_poblacio()
		bool_5, NIF = self.validar_nif()
		bool_6, TEL = self.validar_telf()
		bool_7, forma_pago = self.validar_forma_pago()
		bool_8, num_client = self.validar_num_client()

		if bool_1 and bool_2 and bool_3 and bool_4 and bool_5 and bool_6 and bool_7 and bool_8 :

			os.chdir(carpeta_data)

			delete_from_database('clients', 'num_client', str(num_client).zfill(4))

			fill_database('clients', str(num_client).zfill(4), str(NOMCOM), str(NOMFIS), str(DIR), str(POBLACIO), str(NIF), str(TEL), str(forma_pago))

			if self.pujar_drive_check.isChecked():
				upload_to_drive_database('clients')

			QMessageBox.information(self, 'Information' , 'Client modificat', QMessageBox.Discard)

			self.reinit_dialog()

		else:
			QMessageBox.warning(self, 'Warning!' , 'Dades incorrectes, comprova si el número de client està registrat', QMessageBox.Discard)

	def upload_database(self):
		upload_to_drive_database('clients')
		QMessageBox.information(self, 'Information', 'Dades pujades correctament')

	def reinit_dialog(self):
		self.numclient.setText('')
		self.nomcom.setText('')
		self.direccio.setText('')
		self.nomfis.setText('')
		self.poblacio.setText('')
		self.nif.setText('')
		self.telf.setText('')
		self.formapago.setText('')

		self.numclient.setStyleSheet('')
		self.nomcom.setStyleSheet('')
		self.nomfis.setStyleSheet('')
		self.direccio.setStyleSheet('')
		self.poblacio.setStyleSheet('')
		self.nif.setStyleSheet('')
		self.telf.setStyleSheet('')
		self.formapago.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
			self.pujar_drive_check.setChecked(True)			
		else:
			event.ignore()

class Registre_clients(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		uic.loadUi('RegistreClients.ui', self)

		self.show_table()


	def show_table(self):
		os.chdir(carpeta_data)
		
		if os.path.exists('clients.db'):
			lines = read_database('clients', 'data', 'num_client', 'ASC')

			self.table.setRowCount(len(lines))
			self.table.setColumnCount(8)

			self.table.setHorizontalHeaderLabels(['Nº CLIENT', 'NOM COMERCIAL', 'NOM FISCAL', 'ADREÇA', 'POBLACIÓ', 'NIF', 'TEL', 'FORMA PAGO'])

			font = QFont()
			font.setFamily('Segoe UI Black')
			font.setPointSize(9)

			for i in range(8):
				self.table.horizontalHeaderItem(i).setFont(font)

			llista = []
			for i in range(len(lines)):
				llista.append(lines[i][0])

				for j in range(8):
					if j == 0:
						self.table.setItem(i,j, QTableWidgetItem(lines[i][0])) #num_client
					elif j == 1:
						self.table.setItem(i,j, QTableWidgetItem(lines[i][1])) #nom_com
					elif j == 2:
						self.table.setItem(i,j, QTableWidgetItem(lines[i][2])) #nom_fis
					elif j == 3:
						self.table.setItem(i,j, QTableWidgetItem(lines[i][3])) #adreça
					elif j == 4:
						self.table.setItem(i,j, QTableWidgetItem(lines[i][4])) #poblacio
					elif j == 5:
						self.table.setItem(i,j, QTableWidgetItem(lines[i][5])) #nif
					elif j == 6:
						self.table.setItem(i,j, QTableWidgetItem(lines[i][6])) #tel
					else:
						self.table.setItem(i,j, QTableWidgetItem(lines[i][7])) #forma pago

			self.table.setVerticalHeaderLabels(llista)

			header = self.table.horizontalHeader()
			for i in range(8):
				header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
			for j in range(len(lines)):
				self.table.verticalHeaderItem(j).setFont(font)

class Buscar_client(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('BuscarClient.ui', self)
		
		self.buscador.textChanged.connect(self.validar_buscador)
		self.accepted.connect(self.accept)
		self.rejected.connect(self.reinit_dialog)

	def validar_buscador(self):
		entrada = self.buscador.text()
		validar = re.match("^[a-z\sáéíóúàèìòùäëïöüñç0123456789']+$", entrada, re.I)

		if entrada == '': #Si esta buit bordes grocs							 		
			self.buscador.setStyleSheet('border: 1px solid yellow;')
			return False, entrada

		elif not validar:#Si no es valid bordes vermells
			self.buscador.setStyleSheet('border: 1px solid red;')
			return False, entrada

		else:
			self.buscador.setStyleSheet('border: 1px solid green;')
			return True, entrada

	def accept(self):

		os.chdir(carpeta_data)
		bool1, entrada = self.validar_buscador()

		CONTROL = False

		if bool1 == True:

			if os.path.exists('clients.db'):

				matches, CONTROL = select_from_database('clients', entrada, 'num_client')

				if CONTROL == True:
					self.table.setRowCount(len(matches))
					self.table.setColumnCount(8)

					self.table.setHorizontalHeaderLabels(['Nº CLIENT', 'NOM COMERCIAL', 'NOM FISCAL', 'ADREÇA', 'POBLACIÓ', 'NIF', 'TEL', 'FORMA PAGO'])

					font = QFont()
					font.setFamily('Segoe UI Black')
					font.setPointSize(9)

					for i in range(8):
						self.table.horizontalHeaderItem(i).setFont(font)

					llista = []
					for i in range(len(matches)):
						llista.append('')
						for j in range(8):
							if j == 0:
								self.table.setItem(i,j, QTableWidgetItem(matches[i][0])) #num_client
							elif j == 1:
								self.table.setItem(i,j, QTableWidgetItem(matches[i][1])) #nom_com
							elif j == 2:
								self.table.setItem(i,j, QTableWidgetItem(matches[i][2])) #nom_fis
							elif j == 3:
								self.table.setItem(i,j, QTableWidgetItem(matches[i][3])) #adreça
							elif j == 4:
								self.table.setItem(i,j, QTableWidgetItem(matches[i][4])) #poblacio
							elif j == 5:
								self.table.setItem(i,j, QTableWidgetItem(matches[i][5])) #nif
							elif j == 6:
								self.table.setItem(i,j, QTableWidgetItem(matches[i][6])) #tel
							else:
								self.table.setItem(i,j, QTableWidgetItem(matches[i][7])) #forma pago

					self.table.setVerticalHeaderLabels(llista)

					header = self.table.horizontalHeader()
					for i in range(8):
						header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

				else:
					QMessageBox.warning(self, 'Warning!' , 'Cap coincidència', QMessageBox.Discard)

			else:
				QMessageBox.warning(self, 'Dades incorrectes', 'Encara no has registrat cap client!', QMessageBox.Discard)
		else:
			QMessageBox.warning(self, 'Dades incorrectes', 'Algun caràcter introduït al marcador no és vàlid', QMessageBox.Discard)

	def reinit_dialog(self):
		self.buscador.setText('')
		self.table.setRowCount(0)
		self.table.setColumnCount(0)

		self.buscador.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()


#PRODUCTES
class Nou_producte(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		uic.loadUi('NouProducte.ui', self)

		self.ref_modificar.textChanged.connect(self.validar_ref_mod)
		self.ref_eliminar.textChanged.connect(self.validar_ref_elim)
		self.nom.textChanged.connect(self.validar_nom_prod)

		self.veure_nom_mod.clicked.connect(self.veure_nom_modificar)
		self.veure_nom_elim.clicked.connect(self.veure_nom_eliminar)

		self.registrar.clicked.connect(self.registrar_producte)
		self.modificar.clicked.connect(self.modificar_producte)
		self.eliminar.clicked.connect(self.eliminar_producte)

		self.pujar_drive.clicked.connect(self.upload_database)

	def validar_nom_prod(self):
		nom = self.nom.text()
		validar = re.match('^[a-z\sáéíóúàèìòùäëïöüñç0123456789.-]+$', nom, re.I) #Permetre lletres a-z, espais, accents, numeros
		if nom == '': #Si esta buit bordes grocs							 #re.I ignora majuscules i minuscules			
			self.nom.setStyleSheet('border: 1px solid yellow;')
			return False, nom

		else:
			self.nom.setStyleSheet('border: 1px solid green;')
			return True, nom

		'''
		elif not validar:#Si no es valid bordes vermells
			self.nom.setStyleSheet('border: 1px solid red;')
			return False, nom
		'''

	def validar_ref_mod(self):
		ref = self.ref_modificar.text()
		validar = re.match('^[0123456789]+$', ref)

		if ref == '': #Si esta buit bordes grocs								
			self.ref_modificar.setStyleSheet('border: 1px solid yellow;')
			return False, ref

		elif not validar:#Si no es valid bordes vermells
			self.ref_modificar.setStyleSheet('border: 1px solid red;')
			return False, ref

		else:
			self.ref_modificar.setStyleSheet('border: 1px solid green;')
			return True, ref

	def validar_ref_elim(self):
		ref = self.ref_eliminar.text()
		validar = re.match('^[0123456789]+$', ref)

		if ref == '': #Si esta buit bordes grocs								
			self.ref_eliminar.setStyleSheet('border: 1px solid yellow;')
			return False, ref

		elif not validar:#Si no es valid bordes vermells
			self.ref_eliminar.setStyleSheet('border: 1px solid red;')
			return False, ref

		else:
			self.ref_eliminar.setStyleSheet('border: 1px solid green;')
			return True, ref

	def veure_nom_modificar(self):
		os.chdir(carpeta_data)

		control, ref = self.validar_ref_mod()

		if not os.path.exists('cataleg.db'):
			QMessageBox.warning(self, 'Warning!', 'No existeix catàleg!')
		elif control == False:
			QMessageBox.warning(self, 'Warning!', 'Referència no vàlida!')
		else:
			prod = select_from_database_general('cataleg', 'data',  ref, 'ref', 'ref', 'ASC')

			if len(prod) != 0:
				self.nom_modificar.setText(prod[0][1])
				self.preu_mod_prod.setValue(prod[0][2])
			else:
				QMessageBox.warning(self, 'Warning!', 'Referència no registrada')

	def veure_nom_eliminar(self):
		os.chdir(carpeta_data)

		control, ref = self.validar_ref_elim()

		if not os.path.exists('cataleg.db'):
			QMessageBox.warning(self, 'Warning!', 'No existeix catàleg!')	
		elif control == False:
			QMessageBox.warning(self, 'Warning!', 'Referència no vàlida!')
		else:
			prod = select_from_database_general('cataleg', 'data',  ref, 'ref', 'ref', 'ASC')
			if len(prod) != 0:
				self.nom_eliminar.setText(prod[0][1])
				self.preu_elim_prod.setValue(prod[0][2])
			else:
				QMessageBox.warning(self, 'Warning!', 'Referència no registrada')

	def eliminar_producte(self):
		os.chdir(carpeta_data)

		control, ref = self.validar_ref_elim()

		if not os.path.exists('cataleg.db'):
			QMessageBox.warning(self, 'Warning!', 'No existeix catàleg!')
		elif control == False:
			QMessageBox.warning(self, 'Warning!', 'Referència no vàlida!')
		else:
			delete_from_database('cataleg', 'ref', ref)

			if self.pujar_drive_check.isChecked():
				upload_to_drive_database('cataleg')

			QMessageBox.information(self, 'Information', 'Producte eliminat correctament!')
			self.reinit_dialog()

	def modificar_producte(self):
		os.chdir(carpeta_data)

		control, ref = self.validar_ref_mod()
		prod = self.nom_modificar.text()
		preu = self.preu_mod_prod.value()

		if self.nom_modificar.text() == '':
			os.chdir(carpeta_data)

			control, ref = self.validar_ref_mod()

			if not os.path.exists('cataleg.db'):
				QMessageBox.warning(self, 'Warning!', 'No existeix catàleg!')
			elif control == False:
				QMessageBox.warning(self, 'Warning!', 'Referència no vàlida!')
			else:
				prod = select_from_database_general('cataleg', 'data',  ref, 'ref', 'ref', 'ASC')

				if len(prod) != 0:
					prod = prod[0][1]
				else:
					QMessageBox.warning(self, 'Warning!', 'Referència no registrada')

		if not os.path.exists('cataleg.db'):
			QMessageBox.warning(self, 'Warning!', 'No existeix catàleg!')
		elif control == False:
			QMessageBox.warning(self, 'Warning!', 'Referència no vàlida!')
		elif preu == 0:
			QMessageBox.warning(self, 'Warning!', 'El preu de compra no pot ser 0!')
		else:
			delete_from_database('cataleg', 'ref', ref)
			fill_database_cataleg('cataleg', str(ref).zfill(3), prod, preu)

			if self.pujar_drive_check.isChecked():
				upload_to_drive_database('cataleg')

			QMessageBox.information(self, 'Information', 'Producte modificat correctament!')
			self.reinit_dialog()

	def registrar_producte(self):
		os.chdir(carpeta_data)
		create_database_cataleg('cataleg')
		lines = read_database('cataleg', 'data', 'ref', 'ASC')

		control_nom, prod = self.validar_nom_prod()
		ref = int(lines[len(lines)-1][0]) + 1
		preu = self.preu_nou_prod.value()

		control = True
		for i in range(len(lines)):
			if lines[i][1] == prod:
				control = False
				control_ref = lines[i][0]

		if control == False:
			QMessageBox.warning(self, 'Warning!', 'Aquest producte ja esta registrat amb número de referència %s' % control_ref)

		elif preu == 0:
			QMessageBox.warning(self, 'Warning!', 'El preu del producte no pot ser 0!')

		elif control_nom == False:
			QMessageBox.warning(self, 'Warning!', 'El nom del producte no pot estar buit!')

		else:
			fill_database_cataleg('cataleg', str(ref).zfill(3), prod, preu)
			
			if self.pujar_drive_check.isChecked():
				upload_to_drive_database('cataleg')

			QMessageBox.information(self, 'Information', 'Producte ja registrat amb número de referència %s' % ref)
			self.reinit_dialog()
			

	def upload_database(self):
		upload_to_drive_database('cataleg')
		QMessageBox.information(self, 'Information', 'Dades pujades correctament')

	def reinit_dialog(self):
		self.nom.setText('')
		self.ref_modificar.setText('')
		self.ref_eliminar.setText('')
		self.nom_modificar.setText('')
		self.nom_eliminar.setText('')

		self.preu_mod_prod.setValue(0)
		self.preu_nou_prod.setValue(0)
		self.preu_elim_prod.setValue(0)

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
			self.ref_modificar.setStyleSheet('')
			self.ref_eliminar.setStyleSheet('')
			self.pujar_drive_check.setChecked(True)
		else:
			event.ignore()

class Introduir_preu_producte(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('IntroduirPreu.ui', self)

		self.referencia.textChanged.connect(self.validar_ref)
		self.numclient.textChanged.connect(self.validar_num_client)

		self.seleccionar.clicked.connect(self.validar_dades)
		self.guardar.clicked.connect(self.guardar_preu)
		self.modificar.clicked.connect(self.modificar_preu)

		self.pujar_drive.clicked.connect(self.upload_database)
		
	def validar_ref(self):
		ref = self.referencia.text()
		validar = re.match('^[0123456789]+$', ref)

		if ref == '': #Si esta buit bordes grocs								
			self.referencia.setStyleSheet('border: 1px solid yellow;')
			return False, ref

		elif not validar:#Si no es valid bordes vermells
			self.referencia.setStyleSheet('border: 1px solid red;')
			return False, ref

		else:
			self.referencia.setStyleSheet('border: 1px solid green;')
			return True, ref

	def validar_dades(self):

		control, ref = self.validar_ref()

		os.chdir(carpeta_data)
		if os.path.exists('cataleg.db') and control == True:
			lines = select_from_database_general('cataleg', 'data', ref, 'ref', 'ref', 'ASC')
		
			if len(lines) != 0:
				nom_ref = lines[0][1]

				self.nom.setText(nom_ref)
			else:
				QMessageBox.warning(self, 'Warning!', 'Referència incorrecta o no registrada al catàleg!') 

		elif control == False:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!') 
		else:
			QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap producte!') 

	def validar_num_client(self):
		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 

	def guardar_preu(self):
		control, num_client = self.validar_num_client()
		control_2, ref = self.validar_ref()

		os.chdir(carpeta_data)

		if os.path.exists('clients.db'):

			lines = select_from_database_general('clients', 'data', num_client, 'num_client', 'num_client', 'ASC')

			if control == True and control_2 == True and len(lines) != 0:
				preu_ref = self.preu.value()
				prod = self.nom.text()

				if preu_ref > 0:

					create_database_preus('preus')
					control = fill_database_preus('preus', num_client, ref, prod, preu_ref)

					if control == False:
						QMessageBox.warning(self, 'Warning!', 'El preu per aquest producte i client ja existeix a la base de dades! Si vols modificar-lo, clica el botó \"Modificar preu\"')
					else:

						if self.pujar_drive_check.isChecked(): 
							upload_to_drive_database('preus')

						QMessageBox.information(self, 'Information', 'Dades guardades correctament')
						self.reinit_dialog()

				else:
					QMessageBox.warning(self, 'Warning!', 'Selecciona un preu diferent de 0 per al producte!')
			else:
				QMessageBox.warning(self, 'Warning!', 'Número de client no registrat!')

		else:
			QMessageBox.warning(self, 'Warning!', 'Encara no has reistrat cap client!')

	def upload_database(self):
		upload_to_drive_database('preus')
		QMessageBox.Information(self, 'Information', 'Dades pujades correctament')

	def modificar_preu(self):
		control, num_client = self.validar_num_client()
		control_2, ref = self.validar_ref()

		os.chdir(carpeta_data)

		if os.path.exists('clients.db'):

			lines = select_from_database_general('clients', 'data', num_client, 'num_client', 'num_client', 'ASC')

			if control == True and control_2 == True and len(lines) != 0:
				preu_ref = self.preu.value()
				prod = self.nom.text()

				if preu_ref > 0:

					create_database_preus('preus')
					control = modificar_database_preus('preus', num_client, ref, prod, preu_ref)

					if control == False:
						QMessageBox.warning(self, 'Warning!', 'El preu per aquest producte i client no existeix a la base de dades, per introduir un preu nou clica el botó \"Guardar preu\".')
					else:

						if self.pujar_drive_check.isChecked(): 
							upload_to_drive_database('preus')

						QMessageBox.information(self, 'Information', 'Dades modificades correctament')
						self.reinit_dialog()

				else:
					QMessageBox.warning(self, 'Warning!', 'Selecciona un preu diferent de 0 per al producte!')
			else:
				QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!')
		else:
			QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client!')

	def reinit_dialog(self):
		self.referencia.setText('')
		self.numclient.setText('')
		self.nom.setText('')
		self.preu.setValue(0.)

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
			self.referencia.setStyleSheet('')
			self.numclient.setStyleSheet('')
			self.pujar_drive_check.setChecked(True)
		else:
			event.ignore()

class Cataleg(QDialog): 
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('Cataleg.ui', self)

		self.show.clicked.connect(self.createTable)
 
	def createTable(self):
		os.chdir(carpeta_data)

		if os.path.exists('cataleg.db'):

			if self.order.currentText() == 'Ordre alfabètic':
				lines = read_database('cataleg', 'data', 'prod', 'ASC')
			elif self.order.currentText() == 'Referència asc':
				lines = read_database('cataleg', 'data', 'ref', 'ASC')
			else:
				lines = read_database('cataleg', 'data', 'ref', 'DESC')

			self.table.setRowCount(len(lines))
			self.table.setColumnCount(3)

			header = self.table.horizontalHeader()       
			header.setSectionResizeMode(1, QHeaderView.Stretch)
			header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
			header.setSectionResizeMode(2, QHeaderView.ResizeToContents)


			self.table.setHorizontalHeaderLabels(['REF', 'PRODUCTE', 'PREU DE COMPRA'])

			font = QFont()
			font.setFamily('Segoe UI Black')
			font.setPointSize(9)

			for i in range(3):
				self.table.horizontalHeaderItem(i).setFont(font)

			for i in range(len(lines)):
				for j in range(3):
					self.table.setItem(i,j, QTableWidgetItem(str(lines[i][j])))
				

			llista = []
			for i in range(len(lines)):
				llista.append('')
			self.table.setVerticalHeaderLabels(llista)

		else:
			QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap producte!')

	def reinit_dialog(self):
		self.table.clearContents()

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Veure_preus(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('VeurePreus.ui', self)

		self.show_table()
		self.numclient.textChanged.connect(self.validar_num_client)
		self.referencia.textChanged.connect(self.validar_ref)
		self.seleccionar.clicked.connect(self.show_price_ref)

	def validar_num_client(self):

		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 

	def validar_ref(self):
		ref = self.referencia.text()
		validar = re.match('^[0123456789]+$', ref)

		if ref == '': #Si esta buit bordes grocs								
			self.referencia.setStyleSheet('border: 1px solid yellow;')
			return False, ref

		elif not validar:#Si no es valid bordes vermells
			self.referencia.setStyleSheet('border: 1px solid red;')
			return False, ref

		else:
			self.referencia.setStyleSheet('border: 1px solid green;')
			return True, ref

	def show_table(self):
		os.chdir(carpeta_data)
		if os.path.exists('cataleg.db') and os.path.exists('preus.db'):
			referencies = read_database('cataleg', 'data', 'ref', 'ASC')
			clients = read_database('clients', 'data', 'num_client', 'ASC')
			preus = read_database('preus', 'data', 'ref', 'ASC')

			self.table.setRowCount(len(clients))
			self.table.setColumnCount(len(referencies) + 1)

			horitzontal_labels = ['NUM. CLIENT / REF']
			vertical_labels = []

			for i in range(len(referencies)): horitzontal_labels.append(str(i+1).zfill(3))

			for i in range(len(clients)):
				vertical_labels.append(clients[i][0])
				for j in range(len(referencies)+1):
					if j == 0:
						self.table.setItem(i,j, QTableWidgetItem(clients[i][0]))
					else:
						current_price_customer = select_from_database_preus('preus', str(i+1).zfill(4), str(j).zfill(3))
						if len(current_price_customer) == 0:
							self.table.setItem(i,j, QTableWidgetItem('NULL'))
						else:
							self.table.setItem(i,j, QTableWidgetItem(str(current_price_customer[0][3])))

			self.table.setHorizontalHeaderLabels(horitzontal_labels)
			self.table.setVerticalHeaderLabels(vertical_labels)

			header = self.table.horizontalHeader()   
			header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

			font = QFont()
			font.setFamily('Segoe UI Black')
			font.setPointSize(9)

			for i in range(len(referencies)+1):
				self.table.horizontalHeaderItem(i).setFont(font)
			for i in range(len(clients)):
				self.table.verticalHeaderItem(i).setFont(font)

		else:
			#QMessageBox.warning(self, 'Warning!', 'No existeixen les bases de dades del catàleg o preus! ')
			pass

	def show_price_ref(self):
		control, num_client = self.validar_num_client()
		control_ref, ref = self.validar_ref()

		os.chdir(carpeta_data)

		if os.path.exists('preus.db'):

			price_ref_customer = select_from_database_preus('preus', str(num_client).zfill(4), str(ref).zfill(3))

			if control == True and control_ref == True and len(price_ref_customer) != 0:
				self.preu.setText(str(price_ref_customer[0][3]))

			elif control == True and control_ref == True and len(price_ref_customer) == 0:
				self.preu.setText('NULL')
			else:
				QMessageBox.warning(self, 'Warning!', 'Número de client o referència incorrecte')

		else:
			QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap preu!')

	def reinit_dialog(self):
		self.numclient.setText('')
		self.referencia.setText('')
		self.preu.setText('')

		self.referencia.setStyleSheet('')
		self.numclient.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()


#FACTURACIÓ
class Factura(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('Factura.ui', self)

		self.numclient.textChanged.connect(self.validar_num_client)
		self.seleccionar.clicked.connect(self.search)
		self.facturar.clicked.connect(self.fer_factura)

	def show_table(self, num_client):
		os.chdir(carpeta_data)

		if not os.path.exists('preus.db'):
			QMessageBox.warning(self, 'Warning!', 'No has registrat cap preu!')

		else:

			if self.comboBox.currentText() == 'Referència ascendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'ASC')

			elif self.comboBox.currentText() == 'Referència descendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'DESC')

			elif self.comboBox.currentText() == 'Alfabètic':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'prod', 'ASC')

			if len(lines) == 0:
				QMessageBox.warning(self, 'Warning!', 'Aquest client no té cap preu registrat!')

			else:

				self.table.setRowCount(len(lines))
				self.table.setColumnCount(4)

				llista = []
				for i in range(len(lines)):
					llista.append('')
					for j in range(4):
						if j == 0: #UNITS
							sp = QSpinBox()
							sp.setMaximum(9999)
							self.table.setCellWidget(i,j, sp)

						elif j == 1:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][1])) #REF
						elif j == 2:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][2]))
						elif j == 3:#PRICE
							sp = QDoubleSpinBox()
							sp.setDecimals(3)
							sp.setValue(float(lines[i][3]))
							sp.setMaximum(float(lines[i][3]))
							sp.setMinimum(float(lines[i][3]))
							self.table.setCellWidget(i,j, sp)				


				header = self.table.horizontalHeader()   
				header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(2, QHeaderView.Stretch)

				self.table.setHorizontalHeaderLabels(['UNITATS', 'REF', 'PRODUCTE', 'PREU'])
				self.table.setVerticalHeaderLabels(llista)

				font = QFont()
				font.setFamily('Segoe UI Black')
				font.setPointSize(9)

				for i in range(4):
					self.table.horizontalHeaderItem(i).setFont(font)

	def search(self):
		control, num = self.validar_num_client()

		if control == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db') and os.path.exists('preus.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					self.show_table(num)

					self.nomcom.setText(dades[0][1])
					self.nomfis.setText(dades[0][2])
					self.direccio.setText(dades[0][3])
					self.poblacio.setText(dades[0][4])
					self.nif.setText(dades[0][5])
					self.telf.setText(dades[0][6])
					self.formapago.setText(dades[0][7])

					return True, num

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client no has registrat cap preu!')
				return False, 0

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def validar_num_client(self):

		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 

	def validar_client(self):
		control, num = self.validar_num_client()

		if control == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					return True, num

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client!')
				return False, 0

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def fer_factura(self):

		control, num_client = self.validar_client()

		if control == True:

			data = self.calendar.selectedDate().toString("dd/MM/yyyy")

			dia = str(data[0:2]).zfill(2)
			mes = str(data[3:5]).zfill(2)
			ano = str(data[6:]).zfill(4)

			nom_mes = mesos[int(data[3:5])-1]

			ref = []
			prod = []
			units = []	
			preu = []
			base_imponible = []	

			create_database_ventes('ventes', str(ano))
			create_database_ventes('facturacio_ref', str(ano))

			lines = self.table.rowCount()
			
			for i in range(lines):
				current_units = self.table.cellWidget(i,0).value()
				current_ref = self.table.item(i,1).text()
				current_prod = self.table.item(i,2).text().strip('\n')


				if current_units != 0 :
					ref.append(current_ref)
					prod.append(current_prod)
					units.append(current_units)
					
					#Obtenir el preu a partir de la base de dades

					if os.path.exists('preus.db'):
						control_2 = True

						lines = select_from_database_preus('preus', num_client, current_ref)

						if len(lines) != 0:

							current_price = lines[0][3]
							preu.append(current_price)

							base = round(current_units*current_price, 2)
							base_imponible.append(base)

							#Guardar les ventes a la base de dades
							fill_database_ventes('ventes', str(ano), int(current_ref), int(data[3:5]), current_units, 3)
							fill_database_ventes('facturacio_ref', str(ano), int(current_ref), int(data[3:5]), base, 3)

						else :
							control = False
							ref_control = current_ref
							break

					else:
						control_2 = False


			if len(prod) == 0:
				QMessageBox.warning(self, 'Warning!', 'No has seleccionat cap producte!', QMessageBox.Discard)

			elif np.any(np.array(preu) == 0):
				QMessageBox.warning(self, 'Warning!', 'No has indicat el preu d\'algun dels productes seleccionats!', QMessageBox.Discard)

			elif control == False:
				QMessageBox.warning(self, 'Warning!', 'El preu per a la referència %s i pel número de client %s no està guardat a la base de dades' % (ref_control, num_client))

			elif control_2 == False:
				QMessageBox.warning(self, 'Warning', 'No hi ha preus reistrats per cap client!')

			else:
				#Calcular import total

				suma = 0	

				for i in range(len(base_imponible)):
					suma = suma + base_imponible[i]

				suma = round(suma, 2)

				iva = round(0.21 * suma, 2)

				total = round(suma + iva, 2)

				#Fer factura i pujar al drive

				NOMCOM = self.nomcom.text()
				NOMFIS = self.nomfis.text()
				DIR = self.direccio.text()
				NIF = self.nif.text()
				POBLACIO = self.poblacio.text()
				TEL = self.telf.text()
				forma_pago = self.formapago.text()
				dim = len(prod)

				num_fact = assignar_numero_factura('numero_factura', ano)
				factura(carpeta_factures, 'FACTURA', num_client, NOMCOM, NOMFIS, DIR, NIF, TEL, POBLACIO, num_fact, data, forma_pago, dim, ref, prod, units, preu, base_imponible, suma, iva, total) #Plantilla de la factura per al client seleccionat

				os.chdir(carpeta_data)

				#Factura a la base de dades (nom comercial, B.I., I.V.A., total)
				create_database_factures('factures_emeses')
				fill_database_factures('factures_emeses', dia, mes, ano, str(num_fact).zfill(4), suma, 21, total)

				#Facturació per client base de dades
				create_database_ventes('facturacio_clients', ano)
				fill_database_ventes('facturacio_clients', ano, int(num_client), int(data[3:5]), suma, 4)

				#Facturació total base de dades
				create_database_ventes('facturacio_total', 'data')
				fill_database_ventes('facturacio_total', 'data', int(data[6:]), int(data[3:5]), suma, 3)

				upload_to_drive_factura(carpeta_factures, 'Factures', 'FACTURA', num_fact, data, NOMCOM, num_client, 'ventes.db', 'facturacio_clients.db', 'facturacio_total.db', 'factures_emeses.db')

				QMessageBox.information(self, 'Information', 'Factura realitzada correctament!')

				self.reinit_dialog()

	def reinit_dialog(self):
		self.numclient.setText('')
		self.nomcom.setText('')
		self.direccio.setText('')
		self.nomfis.setText('')
		self.poblacio.setText('')
		self.nif.setText('')
		self.telf.setText('')
		self.formapago.setText('')

		self.table.clearContents()

		self.numclient.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Substituir_factura(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('SubstituirFactura.ui', self)

		self.numclient.textChanged.connect(self.validar_num_client)
		self.numfact.textChanged.connect(self.validar_num_factura)
		self.seleccionar.clicked.connect(self.search)
		self.facturar.clicked.connect(self.fer_factura)

	def show_table(self, num_client):
		os.chdir(carpeta_data)

		if not os.path.exists('preus.db'):
			QMessageBox.warning(self, 'Warning!', 'No has registrat cap preu!')

		else:

			if self.comboBox.currentText() == 'Referència ascendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'ASC')

			elif self.comboBox.currentText() == 'Referència descendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'DESC')

			elif self.comboBox.currentText() == 'Alfabètic':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'prod', 'ASC')

			if len(lines) == 0:
				QMessageBox.warning(self, 'Warning!', 'Aquest client no té cap preu registrat!')

			else:

				self.table.setRowCount(len(lines))
				self.table.setColumnCount(4)

				llista = []
				for i in range(len(lines)):
					llista.append('')
					for j in range(4):
						if j == 0: #UNITS
							sp = QSpinBox()
							sp.setMaximum(9999)
							self.table.setCellWidget(i,j, sp)

						elif j == 1:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][1])) #REF
						elif j == 2:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][2]))
						elif j == 3:#PRICE
							sp = QDoubleSpinBox()
							sp.setDecimals(3)
							sp.setValue(float(lines[i][3]))
							sp.setMaximum(float(lines[i][3]))
							sp.setMinimum(float(lines[i][3]))
							self.table.setCellWidget(i,j, sp)				


				header = self.table.horizontalHeader()   
				header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(2, QHeaderView.Stretch)

				self.table.setHorizontalHeaderLabels(['UNITATS', 'REF', 'PRODUCTE', 'PREU'])
				self.table.setVerticalHeaderLabels(llista)

				font = QFont()
				font.setFamily('Segoe UI Black')
				font.setPointSize(9)

				for i in range(4):
					self.table.horizontalHeaderItem(i).setFont(font)
		

	def search(self):
		control_client, num = self.validar_num_client()
		control_factura, num_fact = self.validar_num_factura()

		if control_client == True and control_factura == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db') and os.path.exists('preus.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					self.show_table(num)

					self.nomcom.setText(dades[0][1])
					self.nomfis.setText(dades[0][2])
					self.direccio.setText(dades[0][3])
					self.poblacio.setText(dades[0][4])
					self.nif.setText(dades[0][5])
					self.telf.setText(dades[0][6])
					self.formapago.setText(dades[0][7])

					return True, num

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client o no has registrat cap preu!')
				return False, 0
			
		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def validar_num_client(self):

		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 

	def validar_num_factura(self):
		os.chdir(carpeta_factures)

		num_fact = self.numfact.text()
		validar = re.match('^[0123456789]+$', num_fact)

		if num_fact == '': #Si esta buit bordes grocs								
			self.numfact.setStyleSheet('border: 1px solid yellow;')
			return False, num_fact

		elif not validar:#Si no es valid bordes vermells
			self.numfact.setStyleSheet('border: 1px solid red;')
			return False, num_fact

		else:
			self.numfact.setStyleSheet('border: 1px solid green;')
			return True, num_fact 

	def validar_client(self):
		control, num = self.validar_num_client()

		if control == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					return True, num
			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client!')

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def fer_factura(self):

		control_client, num_client = self.validar_client()

		data = self.calendar.selectedDate().toString("dd/MM/yyyy")
		num_fact = self.numfact.text()

		dia = str(data[0:2]).zfill(2)
		mes_numero = str(data[3:5]).zfill(2)
		ano = str(data[6:]).zfill(4)

		name_fact = 'FACTURA_%s' % num_fact

		mes = mesos[int(data[3:5])-1]
		año = data[6:]

		if not os.path.exists(carpeta_factures + '\%s_%s' % (mes, año)):
			QMessageBox.warning(self, 'Warning!', 'No has realitzat cap factura pel mes i any de la data seleccionada!')
		else:
			os.chdir(carpeta_factures + '\%s_%s' % (mes, año))

			list_files = os.listdir()

			control_factura = False

			for file in list_files:
				if file[0:12] == name_fact:
					control_factura = True
					os.remove(file)
					break
				else:
					control_factura = False

			if control_factura == False:
				QMessageBox.warning(self, 'Warning!', 'Aquest número de factura no existeix!')

			elif control_client == True:

				ref = []
				prod = []
				units = []	
				preu = []
				base_imponible = []	

				lines = self.table.rowCount()
				
				for i in range(lines):
					current_units = self.table.cellWidget(i,0).value()
					current_ref = self.table.item(i,1).text()
					current_prod = self.table.item(i,2).text().strip('\n')

					if current_units != 0 :
						ref.append(current_ref)
						prod.append(current_prod)
						units.append(current_units)

						#Obtenir el preu a partir de la base de dades
						os.chdir(carpeta_data)
						lines = select_from_database_preus('preus', num_client, current_ref)

						if len(lines) != 0:

							current_price = lines[0][3]
							preu.append(current_price)

							base_imponible.append(round(current_units*current_price, 2))
							control = True

						else :
							control = False
							ref_control = current_ref
							break

				if len(prod)== 0:
					QMessageBox.warning(self, 'Warning!', 'No has seleccionat cap producte!', QMessageBox.Discard)

				elif np.any(np.array(preu) == 0):
					QMessageBox.warning(self, 'Warning!', 'No has indicat el preu d\'algun dels productes seleccionats!', QMessageBox.Discard)

				elif control == False:
					QMessageBox.warning(self, 'Warning!', 'El preu per a la referència %s i pel número de client %s no està guardat a la base de dades' % (ref_control, num_client))

				else:
					#Calcular import total

					suma = 0	

					for i in range(len(base_imponible)):
						suma = suma + base_imponible[i]

					suma = round(suma, 2)

					iva = round(0.21 * suma, 2)

					total = round(suma + iva, 2)

					#Fer factura i pujar al drive

					NOMCOM = self.nomcom.text()
					NOMFIS = self.nomfis.text()
					DIR = self.direccio.text()
					NIF = self.nif.text()
					POBLACIO = self.poblacio.text()
					TEL = self.telf.text()
					forma_pago = self.formapago.text()
					dim = len(prod)

					factura(carpeta_factures, 'FACTURA', num_client, NOMCOM, NOMFIS, DIR, NIF, TEL, POBLACIO, num_fact, data, forma_pago, dim, ref, prod, units, preu, base_imponible, suma, iva, total) #Plantilla de la factura per al client seleccionat
					
					#Factura a la base de dades (nom comercial, B.I., I.V.A., total)
					os.chdir(carpeta_data)

					create_database_factures('factures_emeses')
					delete_from_database('factures_emeses', 'nom', str(num_fact).zfill(4))
					fill_database_factures('factures_emeses', dia, mes_numero, ano, str(num_fact).zfill(4), suma, 21, total)

					upload_to_drive_factura(carpeta_factures, 'Factures', 'FACTURA', num_fact, data, NOMCOM, num_client, 'ventes.db', 'facturacio_clients.db', 'facturacio_total.db', 'factures_emeses.db')

					QMessageBox.information(self, 'Information', 'Factura modificada correctament!')

					self.reinit_dialog()

	def reinit_dialog(self):
		self.numclient.setText('')
		self.nomcom.setText('')
		self.direccio.setText('')
		self.nomfis.setText('')
		self.poblacio.setText('')
		self.nif.setText('')
		self.telf.setText('')
		self.formapago.setText('')
		self.numfact.setText('')

		self.table.clearContents()

		self.numclient.setStyleSheet('')
		self.numfact.setStyleSheet('')
			 
	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Abonos(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('Abono.ui', self)

		self.setWindowTitle('Abonos')
		self.facturar.setText('Realitzar abono')

		self.numclient.textChanged.connect(self.validar_num_client)
		self.seleccionar.clicked.connect(self.search)
		self.facturar.clicked.connect(self.fer_factura)

	def show_table(self, num_client):
		os.chdir(carpeta_data)

		if not os.path.exists('preus.db'):
			QMessageBox.warning(self, 'Warning!', 'No has registrat cap preu!')

		else:

			if self.comboBox.currentText() == 'Referència ascendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'ASC')

			elif self.comboBox.currentText() == 'Referència descendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'DESC')

			elif self.comboBox.currentText() == 'Alfabètic':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'prod', 'ASC')

			if len(lines) == 0:
				QMessageBox.warning(self, 'Warning!', 'Aquest client no té cap preu registrat!')

			else:

				self.table.setRowCount(len(lines))
				self.table.setColumnCount(4)

				llista = []
				for i in range(len(lines)):
					llista.append('')
					for j in range(4):
						if j == 0: #UNITS
							sp = QSpinBox()
							sp.setMaximum(9999)
							self.table.setCellWidget(i,j, sp)

						elif j == 1:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][1])) #REF
						elif j == 2:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][2]))
						elif j == 3:#PRICE
							sp = QDoubleSpinBox()
							sp.setDecimals(3)
							sp.setValue(float(lines[i][3]))
							sp.setMaximum(float(lines[i][3]))
							sp.setMinimum(float(lines[i][3]))
							self.table.setCellWidget(i,j, sp)				


				header = self.table.horizontalHeader()   
				header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(2, QHeaderView.Stretch)

				self.table.setHorizontalHeaderLabels(['UNITATS', 'REF', 'PRODUCTE', 'PREU'])
				self.table.setVerticalHeaderLabels(llista)

				font = QFont()
				font.setFamily('Segoe UI Black')
				font.setPointSize(9)

				for i in range(4):
					self.table.horizontalHeaderItem(i).setFont(font)

	def search(self):
		control, num = self.validar_num_client()

		if control == True:
			os.chdir(carpeta_data)

			if os.path.exists('clients.db') and os.path.exists('preus.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					self.show_table(num)

					self.nomcom.setText(dades[0][1])
					self.nomfis.setText(dades[0][2])
					self.direccio.setText(dades[0][3])
					self.poblacio.setText(dades[0][4])
					self.nif.setText(dades[0][5])
					self.telf.setText(dades[0][6])
					self.formapago.setText(dades[0][7])

					return True, num

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client o encara no has registrat cap preu!')
				return False, 0

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def validar_num_client(self):

		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 

	def validar_client(self):
		control, num = self.validar_num_client()

		if control == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					return True, num

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client!')
				return False, 0

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0


	def fer_factura(self):

		control, num_client = self.validar_client()

		if control == True:

			data = self.calendar.selectedDate().toString("dd/MM/yyyy")

			dia = str(data[0:2]).zfill(2)
			mes = str(data[3:5]).zfill(2)
			ano = str(data[6:]).zfill(4)

			nom_mes = mesos[int(data[3:5])-1]

			ref = []
			prod = []
			units = []	
			preu = []
			base_imponible = []	

			create_database_ventes('ventes', data[6:])
			create_database_ventes('facturacio_ref', data[6:])

			lines = self.table.rowCount()
			
			for i in range(lines):
				current_units = self.table.cellWidget(i,0).value()
				current_ref = self.table.item(i,1).text()
				current_prod = self.table.item(i,2).text().strip('\n')

				if current_units != 0 :
					ref.append(current_ref)
					prod.append(current_prod)
					units.append(current_units)
					
					#Obtenir el preu a partir de la base de dades
					lines = select_from_database_preus('preus', num_client, current_ref)

					if len(lines) != 0:

						current_price = -lines[0][3]
						preu.append(current_price)

						base = round(current_units*current_price, 2)
						base_imponible.append(base)

						#Guardar les ventes a la base de dades
						fill_database_ventes('ventes', data[6:], int(current_ref), int(data[3:5]), -current_units, 3)
						fill_database_ventes('facturacio_ref', str(ano), int(current_ref), int(data[3:5]), base, 3)

					else :
						control = False
						ref_control = current_ref
						break


			if len(prod) == 0:
				QMessageBox.warning(self, 'Warning!', 'No has seleccionat cap producte!', QMessageBox.Discard)

			elif np.any(np.array(preu) == 0):
				QMessageBox.warning(self, 'Warning!', 'No has indicat el preu d\'algun dels productes seleccionats!', QMessageBox.Discard)

			elif control == False:
				QMessageBox.warning(self, 'Warning!', 'El preu per a la referència %s i pel número de client %s no està guardat a la base de dades' % (ref_control, num_client))

			elif not os.path.exists('factures_emeses.db'):
				QMessageBox.warning(self, 'Warning!', 'No pots fer un abono si no has realitzat encara cap factura!')
			else:
				#Calcular import total

				suma = 0	

				for i in range(len(base_imponible)):
					suma = suma + base_imponible[i]

				suma = round(suma, 2)

				iva = round(0.21 * suma, 2)

				total = round(suma + iva, 2)

				#Fer factura i pujar al drive

				NOMCOM = self.nomcom.text()
				NOMFIS = self.nomfis.text()
				DIR = self.direccio.text()
				NIF = self.nif.text()
				POBLACIO = self.poblacio.text()
				TEL = self.telf.text()
				forma_pago = self.formapago.text()
				dim = len(prod)

				num_fact = assignar_numero_factura('numero_abono', ano)

				if self.tipo_abono.currentText() == 'Factura':
					tipo = 'ABONO_FACTURA'

					os.chdir(carpeta_data)

					#SUMA JA ÉS NEATIVA!!!
					#Factura a la base de dades (nom comercial, B.I., I.V.A., total)
					delete_database_factures('factures_emeses', dia, mes, ano, -suma, 21, -total)

					#Facturació per client base de dades
					fill_database_ventes('facturacio_clients', data[6:], int(num_client), int(data[3:5]), suma, 4)

					#Facturació total base de dades
					fill_database_ventes('facturacio_total', 'data', int(data[6:]), int(data[3:5]), suma, 3)

				else:
					tipo = 'ABONO_ALBARAN'

					fill_database_general('CompanyName', 'albaranes(num_client, num_albaran, data, base_imp, iva, total)', '(?,?,?,?,?,?)', [str(num_client).zfill(4), str(num_fact).zfill(4), '%s-%s-%s' % (ano, mes, dia), suma, iva, total])

				factura(carpeta_abonos, tipo, num_client, NOMCOM, NOMFIS, DIR, NIF, TEL, POBLACIO, num_fact, data, forma_pago, dim, ref, prod, units, preu, base_imponible, suma, iva, total) #Plantilla de la factura per al client seleccionat

				upload_to_drive_factura(carpeta_abonos, 'Abonos', tipo, num_fact, data, NOMCOM, num_client, 'ventes.db', 'facturacio_clients.db', 'facturacio_total.db', 'factures_emeses.db')

				QMessageBox.information(self, 'Information', 'Abono realitzat correctament!')

				self.reinit_dialog()

	def reinit_dialog(self):
		self.numclient.setText('')
		self.nomcom.setText('')
		self.direccio.setText('')
		self.nomfis.setText('')
		self.poblacio.setText('')
		self.nif.setText('')
		self.telf.setText('')
		self.formapago.setText('')

		self.table.clearContents()

		self.numclient.setStyleSheet('')
		self.nomcom.setStyleSheet('')
		self.direccio.setStyleSheet('')
		self.nomfis.setStyleSheet('')
		self.poblacio.setStyleSheet('')
		self.nif.setStyleSheet('')
		self.telf.setStyleSheet('')
		self.formapago.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Albaran(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('Factura.ui', self)

		self.setWindowTitle('Albaran')
		self.facturar.setText('Realitzar albaran')

		self.numclient.textChanged.connect(self.validar_num_client)
		self.seleccionar.clicked.connect(self.search)
		self.facturar.clicked.connect(self.fer_factura)

	def show_table(self, num_client):
		os.chdir(carpeta_data)

		if not os.path.exists('preus.db'):
			QMessageBox.warning(self, 'Warning!', 'No has registrat cap preu!')

		else:

			if self.comboBox.currentText() == 'Referència ascendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'ASC')

			elif self.comboBox.currentText() == 'Referència descendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'DESC')

			elif self.comboBox.currentText() == 'Alfabètic':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'prod', 'ASC')

			if len(lines) == 0:
				QMessageBox.warning(self, 'Warning!', 'Aquest client no té cap preu registrat!')

			else:

				self.table.setRowCount(len(lines))
				self.table.setColumnCount(4)

				llista = []
				for i in range(len(lines)):
					llista.append('')
					for j in range(4):
						if j == 0: #UNITS
							sp = QSpinBox()
							sp.setMaximum(9999)
							self.table.setCellWidget(i,j, sp)

						elif j == 1:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][1])) #REF
						elif j == 2:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][2]))
						elif j == 3:#PRICE
							sp = QDoubleSpinBox()
							sp.setDecimals(3)
							sp.setValue(float(lines[i][3]))
							sp.setMaximum(float(lines[i][3]))
							sp.setMinimum(float(lines[i][3]))
							self.table.setCellWidget(i,j, sp)				


				header = self.table.horizontalHeader()   
				header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(2, QHeaderView.Stretch)

				self.table.setHorizontalHeaderLabels(['UNITATS', 'REF', 'PRODUCTE', 'PREU'])
				self.table.setVerticalHeaderLabels(llista)

				font = QFont()
				font.setFamily('Segoe UI Black')
				font.setPointSize(9)

				for i in range(4):
					self.table.horizontalHeaderItem(i).setFont(font)

	def search(self):
		control, num = self.validar_num_client()

		if control == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db') and os.path.exists('preus.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					self.show_table(num)

					self.nomcom.setText(dades[0][1])
					self.nomfis.setText(dades[0][2])
					self.direccio.setText(dades[0][3])
					self.poblacio.setText(dades[0][4])
					self.nif.setText(dades[0][5])
					self.telf.setText(dades[0][6])
					self.formapago.setText(dades[0][7])

					return True, num

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client no has registrat cap preu!')
				return False, 0

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def validar_num_client(self):

		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 

	def validar_client(self):
		control, num = self.validar_num_client()

		if control == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					return True, num

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client!')
				return False, 0

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def fer_factura(self):

		control, num_client = self.validar_client()

		if control == True:

			data = self.calendar.selectedDate().toString("dd/MM/yyyy")

			dia = str(data[0:2]).zfill(2)
			mes = str(data[3:5]).zfill(2)
			ano = str(data[6:]).zfill(4)

			nom_mes = mesos[int(data[3:5])-1]

			ref = []
			prod = []
			units = []	
			preu = []
			base_imponible = []	

			create_database_ventes('ventes', str(ano))
			create_database_ventes('facturacio_ref', str(ano))

			lines = self.table.rowCount()
			
			for i in range(lines):
				current_units = self.table.cellWidget(i,0).value()
				current_ref = self.table.item(i,1).text()
				current_prod = self.table.item(i,2).text().strip('\n')


				if current_units != 0 :
					ref.append(current_ref)
					prod.append(current_prod)
					units.append(current_units)
					
					#Obtenir el preu a partir de la base de dades

					if os.path.exists('preus.db'):
						control_2 = True

						lines = select_from_database_preus('preus', num_client, current_ref)

						if len(lines) != 0:

							current_price = lines[0][3]
							preu.append(current_price)

							base = round(current_units*current_price, 2)
							base_imponible.append(base)

							#Guardar les ventes a la base de dades
							fill_database_ventes('ventes', str(ano), int(current_ref), int(data[3:5]), current_units, 3)
							fill_database_ventes('facturacio_ref', str(ano), int(current_ref), int(data[3:5]), base, 3)

						else :
							control = False
							ref_control = current_ref
							break

					else:
						control_2 = False


			if len(prod) == 0:
				QMessageBox.warning(self, 'Warning!', 'No has seleccionat cap producte!', QMessageBox.Discard)

			elif np.any(np.array(preu) == 0):
				QMessageBox.warning(self, 'Warning!', 'No has indicat el preu d\'algun dels productes seleccionats!', QMessageBox.Discard)

			elif control == False:
				QMessageBox.warning(self, 'Warning!', 'El preu per a la referència %s i pel número de client %s no està guardat a la base de dades' % (ref_control, num_client))

			elif control_2 == False:
				QMessageBox.warning(self, 'Warning', 'No hi ha preus reistrats per cap client!')

			else:
				#Calcular import total

				suma = 0	

				for i in range(len(base_imponible)):
					suma = suma + base_imponible[i]

				suma = round(suma, 2)

				iva = round(0.21 * suma, 2)

				total = round(suma + iva, 2)

				#Fer factura i pujar al drive

				NOMCOM = self.nomcom.text()
				NOMFIS = self.nomfis.text()
				DIR = self.direccio.text()
				NIF = self.nif.text()
				POBLACIO = self.poblacio.text()
				TEL = self.telf.text()
				forma_pago = self.formapago.text()
				dim = len(prod)

				num_fact = assignar_numero_factura('numero_albaran', ano)
				factura(carpeta_albaranes, 'ALBARAN', num_client, NOMCOM, NOMFIS, DIR, NIF, TEL, POBLACIO, num_fact, data, forma_pago, dim, ref, prod, units, preu, base_imponible, suma, iva, total) #Plantilla de la factura per al client seleccionat

				#Albaran a la base de dades (nom comercial, B.I., I.V.A., total)
				os.chdir(carpeta_data)

				tablas = [
					"""
						CREATE TABLE IF NOT EXISTS albaranes(
							num_client TEXT NOT NULL,
							num_albaran TEXT NOT NULL,
							data TEXT NOT NULL,
							base_imp REAL NOT NULL,
							iva REAL NOT NULL,
							total REAL NOT NULL
						);
					"""
				]

				#Albaran a la base de dades
				create_database('CompanyName', tablas)
				fill_database_general('CompanyName', 'albaranes(num_client, num_albaran, data, base_imp, iva, total)', '(?,?,?,?,?,?)', [str(num_client).zfill(4), str(num_fact).zfill(4), '%s-%s-%s' % (ano, mes, dia), suma, iva, total])

				upload_to_drive_factura(carpeta_albaranes, 'Albaranes', 'ALBARAN', num_fact, data, NOMCOM, num_client, 'ventes.db', 'facturacio_clients.db', 'facturacio_total.db', 'factures_emeses.db')

				QMessageBox.information(self, 'Information', 'Albaran realitzat correctament!')

				self.reinit_dialog()

	def reinit_dialog(self):
		self.numclient.setText('')
		self.nomcom.setText('')
		self.direccio.setText('')
		self.nomfis.setText('')
		self.poblacio.setText('')
		self.nif.setText('')
		self.telf.setText('')
		self.formapago.setText('')

		self.table.clearContents()

		self.numclient.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Substituir_albaran(QDialog): #Creating!
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('SubstituirFactura.ui', self)

		self.setWindowTitle('Substituir albaran')
		self.facturar.setText('Substituir')
		self.label_num_fact.setText('Número albaran')

		self.numclient.textChanged.connect(self.validar_num_client)
		self.numfact.textChanged.connect(self.validar_num_factura)
		self.seleccionar.clicked.connect(self.search)
		self.facturar.clicked.connect(self.fer_factura)

	def show_table(self, num_client):
		os.chdir(carpeta_data)

		if not os.path.exists('preus.db'):
			QMessageBox.warning(self, 'Warning!', 'No has registrat cap preu!')

		else:

			if self.comboBox.currentText() == 'Referència ascendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'ASC')

			elif self.comboBox.currentText() == 'Referència descendent':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'ref', 'DESC')

			elif self.comboBox.currentText() == 'Alfabètic':
				lines = select_from_database_general('preus', 'data', str(num_client).zfill(4), 'num_client', 'prod', 'ASC')

			if len(lines) == 0:
				QMessageBox.warning(self, 'Warning!', 'Aquest client no té cap preu registrat!')

			else:

				self.table.setRowCount(len(lines))
				self.table.setColumnCount(4)

				llista = []
				for i in range(len(lines)):
					llista.append('')
					for j in range(4):
						if j == 0: #UNITS
							sp = QSpinBox()
							sp.setMaximum(9999)
							self.table.setCellWidget(i,j, sp)

						elif j == 1:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][1])) #REF
						elif j == 2:
							self.table.setItem(i,j, QTableWidgetItem(lines[i][2]))
						elif j == 3:#PRICE
							sp = QDoubleSpinBox()
							sp.setDecimals(3)
							sp.setValue(float(lines[i][3]))
							sp.setMaximum(float(lines[i][3]))
							sp.setMinimum(float(lines[i][3]))
							self.table.setCellWidget(i,j, sp)				


				header = self.table.horizontalHeader()   
				header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
				header.setSectionResizeMode(2, QHeaderView.Stretch)

				self.table.setHorizontalHeaderLabels(['UNITATS', 'REF', 'PRODUCTE', 'PREU'])
				self.table.setVerticalHeaderLabels(llista)

				font = QFont()
				font.setFamily('Segoe UI Black')
				font.setPointSize(9)

				for i in range(4):
					self.table.horizontalHeaderItem(i).setFont(font)
		
	def search(self):
		control_client, num = self.validar_num_client()
		control_factura, num_fact = self.validar_num_factura()

		if control_client == True and control_factura == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db') and os.path.exists('preus.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					self.show_table(num)

					self.nomcom.setText(dades[0][1])
					self.nomfis.setText(dades[0][2])
					self.direccio.setText(dades[0][3])
					self.poblacio.setText(dades[0][4])
					self.nif.setText(dades[0][5])
					self.telf.setText(dades[0][6])
					self.formapago.setText(dades[0][7])

					return True, num

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client o no has registrat cap preu!')
				return False, 0
			
		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def validar_num_client(self):

		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 

	def validar_num_factura(self):
		os.chdir(carpeta_albaranes)

		num_fact = self.numfact.text()
		validar = re.match('^[0123456789]+$', num_fact)

		if num_fact == '': #Si esta buit bordes grocs								
			self.numfact.setStyleSheet('border: 1px solid yellow;')
			return False, num_fact

		elif not validar:#Si no es valid bordes vermells
			self.numfact.setStyleSheet('border: 1px solid red;')
			return False, num_fact

		else:
			self.numfact.setStyleSheet('border: 1px solid green;')
			return True, num_fact 

	def validar_client(self):
		control, num = self.validar_num_client()

		if control == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					return True, num
			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client!')

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def fer_factura(self):

		control_client, num_client = self.validar_client()

		data = self.calendar.selectedDate().toString("dd/MM/yyyy")
		num_fact = self.numfact.text()

		dia = str(data[0:2]).zfill(2)
		mes_numero = str(data[3:5]).zfill(2)
		ano = str(data[6:]).zfill(4)

		name_fact = 'ALBARAN_%s' % num_fact

		mes = mesos[int(data[3:5])-1]
		año = data[6:]

		if not os.path.exists(carpeta_albaranes + '\%s_%s' % (mes, año)):
			QMessageBox.warning(self, 'Warning!', 'No has realitzat cap albaran pel mes i any de la data seleccionada!')
		else:
			os.chdir(carpeta_albaranes + '\%s_%s' % (mes, año))

			list_files = os.listdir()

			control_factura = False

			for file in list_files:
				if file[0:12] == name_fact:
					control_factura = True
					os.remove(file)
					break
				else:
					control_factura = False

			if control_factura == False:
				QMessageBox.warning(self, 'Warning!', 'Aquest número d\'albaran no existeix!')

			elif control_client == True:

				ref = []
				prod = []
				units = []	
				preu = []
				base_imponible = []	

				lines = self.table.rowCount()
				
				for i in range(lines):
					current_units = self.table.cellWidget(i,0).value()
					current_ref = self.table.item(i,1).text()
					current_prod = self.table.item(i,2).text().strip('\n')

					if current_units != 0 :
						ref.append(current_ref)
						prod.append(current_prod)
						units.append(current_units)

						#Obtenir el preu a partir de la base de dades
						os.chdir(carpeta_data)
						lines = select_from_database_preus('preus', num_client, current_ref)

						if len(lines) != 0:

							current_price = lines[0][3]
							preu.append(current_price)

							base_imponible.append(round(current_units*current_price, 2))
							control = True

						else :
							control = False
							ref_control = current_ref
							break

				if len(prod)== 0:
					QMessageBox.warning(self, 'Warning!', 'No has seleccionat cap producte!', QMessageBox.Discard)

				elif np.any(np.array(preu) == 0):
					QMessageBox.warning(self, 'Warning!', 'No has indicat el preu d\'algun dels productes seleccionats!', QMessageBox.Discard)

				elif control == False:
					QMessageBox.warning(self, 'Warning!', 'El preu per a la referència %s i pel número de client %s no està guardat a la base de dades' % (ref_control, num_client))

				else:
					#Calcular import total

					suma = 0	

					for i in range(len(base_imponible)):
						suma = suma + base_imponible[i]

					suma = round(suma, 2)

					iva = round(0.21 * suma, 2)

					total = round(suma + iva, 2)

					#Fer factura i pujar al drive

					NOMCOM = self.nomcom.text()
					NOMFIS = self.nomfis.text()
					DIR = self.direccio.text()
					NIF = self.nif.text()
					POBLACIO = self.poblacio.text()
					TEL = self.telf.text()
					forma_pago = self.formapago.text()
					dim = len(prod)

					factura(carpeta_albaranes, 'ALBARAN', num_client, NOMCOM, NOMFIS, DIR, NIF, TEL, POBLACIO, num_fact, data, forma_pago, dim, ref, prod, units, preu, base_imponible, suma, iva, total) #Plantilla de la factura per al client seleccionat
					
					#Factura a la base de dades (nom comercial, B.I., I.V.A., total)
					os.chdir(carpeta_data)

					#Factures emeses
					create_database_factures('factures_emeses')
					delete_from_database('factures_emeses', 'nom', str(num_fact).zfill(4))
					fill_database_factures('factures_emeses', dia, mes_numero, ano, str(num_fact).zfill(4), suma, 21, total)

					#Albaranes
					delete_from_database_general('CompanyName', 'albaranes', 'num_albaran', str(num_fact).zfill(4))
					fill_database_general('CompanyName', 'albaranes(num_client, num_albaran, data, base_imp, iva, total)', '(?,?,?,?,?,?)', [str(num_client).zfill(4), num_fact, '%s-%s-%s' % (ano, mes_numero, dia), suma, iva, total])

					upload_to_drive_factura(carpeta_albaranes, 'Albaranes', 'ALBARAN', num_fact, data, NOMCOM, num_client, 'ventes.db', 'facturacio_clients.db', 'facturacio_total.db', 'factures_emeses.db')

					QMessageBox.information(self, 'Information', 'Albaran modificat correctament!')

					self.reinit_dialog()

	def reinit_dialog(self):
		self.numclient.setText('')
		self.nomcom.setText('')
		self.direccio.setText('')
		self.nomfis.setText('')
		self.poblacio.setText('')
		self.nif.setText('')
		self.telf.setText('')
		self.formapago.setText('')
		self.numfact.setText('')

		self.table.clearContents()

		self.numclient.setStyleSheet('')
		self.numfact.setStyleSheet('')
			 
	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Factura_albaranes(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('FacturaAlbaran.ui', self)

		current_date = QDate.currentDate()
		self.data_factura.setDate(current_date)

		self.numclient.textChanged.connect(self.validar_num_client)
		self.seleccionar.clicked.connect(self.search)
		self.facturar.clicked.connect(self.fer_factura)

	def search(self):
		control, num = self.validar_num_client()

		if control == True:

			os.chdir(carpeta_data)

			if os.path.exists('clients.db') and os.path.exists('preus.db'):

				dades = select_from_database_general('clients', 'data', num, 'num_client', 'num_client', 'ASC')

				if len(dades) == 0:
					QMessageBox.warning(self, 'Warning!', 'Client no registrat!', QMessageBox.Discard)
					return False, 0
					
				else:

					self.nomcom.setText(dades[0][1])
					self.nomfis.setText(dades[0][2])
					self.direccio.setText(dades[0][3])
					self.poblacio.setText(dades[0][4])
					self.nif.setText(dades[0][5])
					self.telf.setText(dades[0][6])
					self.formapago.setText(dades[0][7])

					return True, num

			else:
				QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client no has registrat cap preu!')
				return False, 0

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
			return False, 0

	def validar_num_client(self):

		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 

	def fer_factura(self):
		control, num_client = self.search()

		if control == True:

			data_inicial = self.calendar.selectedDate().toString("yyyy-MM-dd")
			data_final = self.calendar_2.selectedDate().toString("yyyy-MM-dd")

			#eConnect to the database
			database = sqlite3.connect('CompanyName.db')
			cursor = database.cursor()

			#Get the albaranes done between the delected dates
			sentencia = "SELECT * FROM albaranes WHERE num_client LIKE '%s' AND data BETWEEN '%s' AND '%s' ORDER BY data ASC" % (num_client, data_inicial, data_final)
			cursor.execute(sentencia)
			lines = cursor.fetchall()

			if len(lines) == 0:
				QMessageBox.warning(self, 'Warning!', 'Cap albaran realitzat per aquest client entre aquestes dates!')

			else:
				array_num_albaran = []
				array_data = []
				array_bi = []
				array_iva = []
				array_total = []

				for i in range(len(lines)):
					array_num_albaran.append(lines[i][1]) #Numero d'albaran
					array_data.append(change_date_format(lines[i][2])) #Data
					array_bi.append(lines[i][3]) #Base imponible
					array_iva.append(lines[i][4]) #IVA
					array_total.append(lines[i][5]) #Total

				suma_bi = np.sum(array_bi)
				suma_iva = np.sum(array_iva)
				suma_total = np.sum(array_total)

				self.data_inicial.setDate(self.calendar.selectedDate())
				self.data_final.setDate(self.calendar_2.selectedDate())

				self.num_albaranes.setValue(len(lines))

				self.bi.setText(str(suma_bi))
				self.iva.setText(str(suma_iva))
				self.total.setText(str(suma_total))

				NOMCOM = self.nomcom.text()
				NOMFIS = self.nomfis.text()
				DIR = self.direccio.text()
				NIF = self.nif.text()
				POBLACIO = self.poblacio.text()
				TEL = self.telf.text()
				forma_pago = self.formapago.text()

				data = self.data_factura.date().toString("dd/MM/yyyy")

				dia = str(data[0:2]).zfill(2)
				mes = str(data[3:5]).zfill(2)
				ano = str(data[6:]).zfill(4)

				num_fact = assignar_numero_factura('numero_factura', ano)
				factura_de_albaranes(carpeta_factures, 'FACTURA', num_client, NOMCOM, NOMFIS, DIR, NIF, TEL, POBLACIO, num_fact, data, forma_pago, array_num_albaran, array_data, array_bi, array_iva, array_total, suma_bi, suma_iva, suma_total)

				os.chdir(carpeta_data)

				#Factura a la base de dades (nom comercial, B.I., I.V.A., total)
				create_database_factures('factures_emeses')
				fill_database_factures('factures_emeses', dia, mes, ano, str(num_fact).zfill(4), suma_bi, 21, suma_total)

				#Facturació per client base de dades
				create_database_ventes('facturacio_clients', ano)
				fill_database_ventes('facturacio_clients', ano, int(num_client), int(data[3:5]), suma_bi, 4)

				#Facturació total base de dades
				create_database_ventes('facturacio_total', 'data')
				fill_database_ventes('facturacio_total', 'data', int(data[6:]), int(data[3:5]), suma_bi, 3)

				upload_to_drive_factura(carpeta_factures, 'Factures', 'FACTURA', num_fact, data, NOMCOM, num_client, 'ventes.db', 'facturacio_clients.db', 'facturacio_total.db', 'factures_emeses.db')					

				QMessageBox.information(self, 'Information', 'Factura realitzada correctament!')

	def reinit_dialog(self):
		self.numclient.setText('')
		self.nomcom.setText('')
		self.direccio.setText('')
		self.nomfis.setText('')
		self.poblacio.setText('')
		self.nif.setText('')
		self.telf.setText('')
		self.formapago.setText('')

		self.numclient.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()
		
class Introduir_factures_rebudes(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('IntroduirFacturesRebudes.ui', self)

		self.data.setDate(QDate.currentDate())
		self.nom.textChanged.connect(self.validar_nom)

		self.introduir.clicked.connect(self.guardar)
		self.eliminar.clicked.connect(self.delete)

		self.pujar_drive.clicked.connect(self.upload_database)

	def validar_nom(self):
		nom = self.nom.text()
		validar = re.match('^[a-z\sáéíóúàèìòùäëïöüñç0123456789.-]+$', nom, re.I) #Permetre lletres a-z, espais, accents, numeros
		if nom == '': #Si esta buit bordes grocs							 #re.I ignora majuscules i minuscules			
			self.nom.setStyleSheet('border: 1px solid yellow;')
			return False, nom

		elif not validar:#Si no es valid bordes vermells
			self.nom.setStyleSheet('border: 1px solid red;')
			return False, nom

		else:
			self.nom.setStyleSheet('border: 1px solid green;')
			return True, nom

	def guardar(self):
		control, nom = self.validar_nom()

		if control == True:
			dia = str(self.data.date().day())
			mes = str(self.data.date().month())
			ano = str(self.data.date().year())

			total = self.importe.value()
			IVA  = self.iva.value()

			if total != 0 and IVA != 0: 

				base_imponible = round(total/(100+IVA) * 100, 2)

				os.chdir(carpeta_data)
				create_database_factures('factures_rebudes')
				fill_database_factures('factures_rebudes', dia, mes, ano, nom, base_imponible, IVA, total)

				if self.pujar_drive_check.isChecked():
					upload_to_drive_database('factures_rebudes')

				QMessageBox.information(self, 'Information', 'Dades enregistrades correctament')
				self.reinit_dialog()

			else:
				QMessageBox.warning(self, 'Warning!', 'L\' import i l\'I.V.A. no poden ser 0')

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes')

	def delete(self):
		control, nom = self.validar_nom()

		if control == True:
			dia = str(self.data.date().day())
			mes = str(self.data.date().month())
			ano = str(self.data.date().year())

			total = self.importe.value()
			IVA  = self.iva.value()

			if total != 0 and IVA != 0: 

				base_imponible = round(total/(100+IVA) * 100, 2)

				os.chdir(carpeta_data)
				create_database_factures('factures_rebudes')
				delete_database_factures('factures_rebudes', dia, mes, ano, base_imponible, IVA, total)

				if self.pujar_drive_check.isChecked():
					upload_to_drive_database('factures_rebudes')

				QMessageBox.information(self, 'Information', 'Dades enregistrades correctament')
				self.reinit_dialog()

			else:
				QMessageBox.warning(self, 'Warning!', 'L\' import i l\'I.V.A. no poden ser 0')

		else:
			QMessageBox.warning(self, 'Warning!', 'Dades incorrectes')

	def upload_database(self):
		upload_to_drive_database('factures_rebudes')
		QMessageBox.information(self, 'Information', 'Dades pujades correctament')

	def reinit_dialog(self):
		self.data.setDate(QDate.currentDate())
		self.nom.setText('')
		self.iva.setValue(0.)
		self.importe.setValue(0.)

		self.nom.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
			self.pujar_drive_check.setChecked(True)
		else:
			event.ignore()

class Factures_rebudes(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('FacturesRebudes.ui', self)

		current_date = QDate.currentDate()
		day = current_date.day()

		self.data_final.setDate(current_date)
		self.data_inicial.setDate(current_date.addDays(-day+1))

		self.seleccionar.clicked.connect(self.show_table)

	def show_table(self):
		dia_inicial = int(self.data_inicial.date().day())
		mes_inicial = int(self.data_inicial.date().month())
		ano_inicial = int(self.data_inicial.date().year())

		dia_final = int(self.data_final.date().day())
		mes_final = int(self.data_final.date().month())
		ano_final = int(self.data_final.date().year())

		os.chdir(carpeta_data)
		if not os.path.exists('factures_rebudes.db'):
			QMessageBox.warning(self, 'Warning!', 'No existeix cap factura rebuda!')

		else:

			lines = read_database_factures('factures_rebudes', 'ASC')

			matches = []
			for i in range(len(lines)):
				if ano_inicial < ano_final :
					if int(lines[i][2]) < ano_final and int(lines[i][2]) > ano_inicial: #Si esta en mig es veuran complets
						matches.append(lines[i])

					elif int(lines[i][2]) == ano_inicial: #Si l'any es el mateix comprovar el mes
						if int(lines[i][1]) > mes_inicial :
							matches.append(lines[i])

						elif int(lines[i][2]) == mes_inicial and int(lines[i][0]) >= dia_inicial: #Comprovar el dia
							matches.append(lines[i])

					elif int(lines[i][2]) == ano_final: #Si l'any es el mateix comprovar el mes
						if int(lines[i][1]) < mes_final: 
							matches.append(lines[i])

						elif int(lines[i][1]) == mes_final and int(lines[i][0]) <= dia_final: #Comprovar el dia
							matches.append(lines[i])

				elif ano_inicial == ano_final and mes_inicial != mes_final:
					if int(lines[i][1]) > mes_inicial and int(lines[i][1]) < mes_final:
						matches.append(lines[i])

					elif int(lines[i][1]) == mes_inicial and int(lines[i][0]) >= dia_inicial:
						matches.append(lines[i])

					elif int(lines[i][1]) == mes_final and int(lines[i][0]) <= dia_final:
						matches.append(lines[i])

				elif ano_inicial == ano_final and mes_inicial == mes_final:
					if int(lines[i][1]) == mes_inicial and int(lines[i][0]) >= dia_inicial and int(lines[i][0]) <= dia_final:
						matches.append(lines[i])
			
			self.table.setRowCount(len(matches))
			self.table.setColumnCount(6)

			self.table.setHorizontalHeaderLabels(['DATA', 'ESTABLIMENT', 'BASE IMPONIBLE', 'IVA %', 'IVA \u20ac', 'TOTAL'])

			font = QFont()
			font.setFamily('Segoe UI Black')
			font.setPointSize(9)

			for i in range(6):
				self.table.horizontalHeaderItem(i).setFont(font)

			llista = []
			suma_bi = 0
			suma_iva = 0
			suma_total = 0

			#display in the table
			for i in range(len(matches)):
				llista.append('')

				suma_bi += matches[i][4]
				suma_total += matches[i][6]

				for j in range(6):
						if j == 0:
							data = str(matches[i][0]).zfill(2) + '/' + str(matches[i][1]).zfill(2) + '/' + str(matches[i][2])
							item = QTableWidgetItem(data)
							item.setTextAlignment(Qt.AlignHCenter)
							self.table.setItem(i,j, item)

						elif j == 4:
							iva = matches[i][5] / 100
							iva_euros = round(iva * matches[i][4], 2)

							suma_iva += iva_euros

							item = QTableWidgetItem(str(iva_euros))
							item.setTextAlignment(Qt.AlignHCenter)
							self.table.setItem(i,j, item)

						elif j == 5:
							item = QTableWidgetItem(str(matches[i][6]))
							item.setTextAlignment(Qt.AlignHCenter)
							self.table.setItem(i,j, item)

						else:
							item = QTableWidgetItem(str(matches[i][j+2]))
							item.setTextAlignment(Qt.AlignHCenter)
							self.table.setItem(i,j, item)

			self.table.setVerticalHeaderLabels(llista)

			header = self.table.horizontalHeader()   
			header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
			header.setSectionResizeMode(1, QHeaderView.Stretch)
			header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
			header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
			header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
			header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

			self.bi_tot.setText(str(round(suma_bi, 2)) + ' \u20ac')
			self.iva_tot.setText(str(round(suma_iva, 2)) + ' \u20ac')
			self.total_tot.setText(str(round(suma_total, 2)) + ' \u20ac')

			self.bi_tot.setStyleSheet('border: 1px solid red;')
			self.iva_tot.setStyleSheet('border: 1px solid red;')
			self.total_tot.setStyleSheet('border: 1px solid red;')

	def reinit_dialog(self):
		self.table.clearContents()
		self.bi_tot.setText('')
		self.iva_tot.setText('')
		self.total_tot.setText('')

		self.bi_tot.setStyleSheet('')
		self.iva_tot.setStyleSheet('')
		self.total_tot.setStyleSheet('')	

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Factures_emeses(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('FacturesRebudes.ui', self)

		self.setWindowTitle('Factures emeses')

		current_date = QDate.currentDate()
		day = current_date.day()

		self.data_final.setDate(current_date)
		self.data_inicial.setDate(current_date.addDays(-day+1))

		self.seleccionar.clicked.connect(self.show_table)

	def show_table(self):
		dia_inicial = int(self.data_inicial.date().day())
		mes_inicial = int(self.data_inicial.date().month())
		ano_inicial = int(self.data_inicial.date().year())

		dia_final = int(self.data_final.date().day())
		mes_final = int(self.data_final.date().month())
		ano_final = int(self.data_final.date().year())

		os.chdir(carpeta_data)
		if not os.path.exists('factures_emeses.db'):
			QMessageBox.warning(self, 'Warning!', 'No existeix cap factura emesa')

		else:

			lines = read_database_factures('factures_emeses', 'ASC')

			matches = []
			for i in range(len(lines)):
				if ano_inicial < ano_final :
					if int(lines[i][2]) < ano_final and int(lines[i][2]) > ano_inicial: #Si esta en mig es veuran complets
						matches.append(lines[i])

					elif int(lines[i][2]) == ano_inicial: #Si l'any es el mateix comprovar el mes
						if int(lines[i][1]) > mes_inicial :
							matches.append(lines[i])

						elif int(lines[i][2]) == mes_inicial and int(lines[i][0]) >= dia_inicial: #Comprovar el dia
							matches.append(lines[i])

					elif int(lines[i][2]) == ano_final: #Si l'any es el mateix comprovar el mes
						if int(lines[i][1]) < mes_final: 
							matches.append(lines[i])

						elif int(lines[i][1]) == mes_final and int(lines[i][0]) <= dia_final: #Comprovar el dia
							matches.append(lines[i])

				elif ano_inicial == ano_final and mes_inicial != mes_final:
					if int(lines[i][1]) > mes_inicial and int(lines[i][1]) < mes_final:
						matches.append(lines[i])

					elif int(lines[i][1]) == mes_inicial and int(lines[i][0]) >= dia_inicial:
						matches.append(lines[i])

					elif int(lines[i][1]) == mes_final and int(lines[i][0]) <= dia_final:
						matches.append(lines[i])

				elif ano_inicial == ano_final and mes_inicial == mes_final:
					if int(lines[i][1]) == mes_inicial and int(lines[i][0]) >= dia_inicial and int(lines[i][0]) <= dia_final:
						matches.append(lines[i])
			
			self.table.setRowCount(len(matches))
			self.table.setColumnCount(6)

			self.table.setHorizontalHeaderLabels(['DATA', 'NUM FACTURA', 'BASE IMPONIBLE', 'IVA %', 'IVA \u20ac', 'TOTAL'])

			font = QFont()
			font.setFamily('Segoe UI Black')
			font.setPointSize(9)

			for i in range(6):
				self.table.horizontalHeaderItem(i).setFont(font)

			llista = []

			suma_bi = 0
			suma_iva = 0
			suma_total = 0

			#display in the table
			for i in range(len(matches)):
				llista.append('')

				suma_bi += matches[i][4]
				suma_total += matches[i][6]

				for j in range(6):
						if j == 0:
							data = str(matches[i][0]).zfill(2) + '/' + str(matches[i][1]).zfill(2) + '/' + str(matches[i][2])
							item = QTableWidgetItem(data)
							item.setTextAlignment(Qt.AlignHCenter)
							self.table.setItem(i,j, item)
							j = 2

						elif j == 4:
							iva = matches[i][5] / 100
							iva_euros = round(iva * matches[i][4], 2)

							suma_iva += iva_euros

							item = QTableWidgetItem(str(iva_euros))
							item.setTextAlignment(Qt.AlignHCenter)
							self.table.setItem(i,j, item)

						elif j == 5:
							item = QTableWidgetItem(str(matches[i][6]))
							item.setTextAlignment(Qt.AlignHCenter)
							self.table.setItem(i,j, item)

						else:
							item = QTableWidgetItem(str(matches[i][j+2]))
							item.setTextAlignment(Qt.AlignHCenter)
							self.table.setItem(i,j, item)

			self.table.setVerticalHeaderLabels(llista)

			header = self.table.horizontalHeader()   
			header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
			header.setSectionResizeMode(1, QHeaderView.Stretch)
			header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
			header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
			header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
			header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

			self.bi_tot.setText(str(round(suma_bi, 2)) + ' \u20ac')
			self.iva_tot.setText(str(round(suma_iva, 2)) + ' \u20ac')
			self.total_tot.setText(str(round(suma_total, 2)) + ' \u20ac')

			self.bi_tot.setStyleSheet('border: 1px solid green;')
			self.iva_tot.setStyleSheet('border: 1px solid green;')
			self.total_tot.setStyleSheet('border: 1px solid green;')

	def reinit_dialog(self):
		self.table.clearContents()
		self.bi_tot.setText('')
		self.iva_tot.setText('')
		self.total_tot.setText('')	

		self.bi_tot.setStyleSheet('')
		self.iva_tot.setStyleSheet('')
		self.total_tot.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Marge(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('Marge.ui', self)

		current_date = QDate.currentDate()
		day = current_date.day()

		self.data_final.setDate(current_date)
		self.data_inicial.setDate(current_date.addDays(-day+1))

		self.dif_bi.textChanged.connect(self.validar_diferencia_bi)
		self.dif_iva.textChanged.connect(self.validar_diferencia_iva)
		self.dif_tot.textChanged.connect(self.validar_diferencia_tot)
		self.beneficis_stock.textChanged.connect(self.validar_beneficis_stock)

		self.bi_tot_1.setStyleSheet('border: 1px solid red;')
		self.iva_tot_1.setStyleSheet('border: 1px solid red;')
		self.total_tot_1.setStyleSheet('border: 1px solid red;')

		self.bi_tot_2.setStyleSheet('border: 1px solid green;')
		self.iva_tot_2.setStyleSheet('border: 1px solid green;')
		self.total_tot_2.setStyleSheet('border: 1px solid green;')

		self.stock.setStyleSheet('border: 1px solid green')

		self.seleccionar.clicked.connect(self.show_table)

	def validar_beneficis_stock(self):
		x = self.beneficis_stock.text()
		
		if float(x[0:len(x)-2].replace(',', '.')) < 0: #Si es negatiu son perdues
			self.beneficis_stock.setStyleSheet('border: 1px solid red;')

		elif float(x[0:len(x)-2].replace(',', '.')) == 0:
			self.beneficis_stock.setStyleSheet('border: 1px solid yellow;')

		else:
			self.beneficis_stock.setStyleSheet('border: 1px solid green;')

	def validar_diferencia_bi(self):
		x = self.dif_bi.text()

		x = float(x[0:len(x)-2].replace(',', '.'))
		
		if x < 0: #Si es negatiu son perdues
			self.dif_bi.setStyleSheet('border: 1px solid red;')

		elif x == 0:
			self.dif_bi.setStyleSheet('border: 1px solid yellow;')			

		else:
			self.dif_bi.setStyleSheet('border: 1px solid green;')

	def validar_diferencia_iva(self):
		x = self.dif_iva.text()
		
		if float(x[0:len(x)-2].replace(',', '.')) < 0: #Si es negatiu son perdues
			self.dif_iva.setStyleSheet('border: 1px solid red;')

		elif float(x[0:len(x)-2].replace(',', '.')) == 0:
			self.dif_iva.setStyleSheet('border: 1px solid yellow;')

		else:
			self.dif_iva.setStyleSheet('border: 1px solid green;')

	def validar_diferencia_tot(self):
		x = self.dif_tot.text()
		
		if float(x[0:len(x)-2].replace(',', '.')) < 0: #Si es negatiu son perdues
			self.dif_tot.setStyleSheet('border: 1px solid red;')

		elif float(x[0:len(x)-2].replace(',', '.')) == 0:
			self.dif_tot.setStyleSheet('border: 1px solid yellow;')

		else:
			self.dif_tot.setStyleSheet('border: 1px solid green;')

	def factures_taula(self, nom, headerlabel_array, table, bi, y, total):

		dia_inicial = int(self.data_inicial.date().day())
		mes_inicial = int(self.data_inicial.date().month())
		ano_inicial = int(self.data_inicial.date().year())

		dia_final = int(self.data_final.date().day())
		mes_final = int(self.data_final.date().month())
		ano_final = int(self.data_final.date().year())

		os.chdir(carpeta_data)
		lines = read_database_factures('%s' % nom, 'ASC')

		matches = []
		for i in range(len(lines)):
			if ano_inicial < ano_final :
				if int(lines[i][2]) < ano_final and int(lines[i][2]) > ano_inicial: #Si esta en mig es veuran complets
					matches.append(lines[i])

				elif int(lines[i][2]) == ano_inicial: #Si l'any es el mateix comprovar el mes
					if int(lines[i][1]) > mes_inicial :
						matches.append(lines[i])

					elif int(lines[i][2]) == mes_inicial and int(lines[i][0]) >= dia_inicial: #Comprovar el dia
						matches.append(lines[i])

				elif int(lines[i][2]) == ano_final: #Si l'any es el mateix comprovar el mes
					if int(lines[i][1]) < mes_final: 
						matches.append(lines[i])

					elif int(lines[i][1]) == mes_final and int(lines[i][0]) <= dia_final: #Comprovar el dia
						matches.append(lines[i])

			elif ano_inicial == ano_final and mes_inicial != mes_final:
				if int(lines[i][1]) > mes_inicial and int(lines[i][1]) < mes_final:
					matches.append(lines[i])

				elif int(lines[i][1]) == mes_inicial and int(lines[i][0]) >= dia_inicial:
					matches.append(lines[i])

				elif int(lines[i][1]) == mes_final and int(lines[i][0]) <= dia_final:
					matches.append(lines[i])

			elif ano_inicial == ano_final and mes_inicial == mes_final:
				if int(lines[i][1]) == mes_inicial and int(lines[i][0]) >= dia_inicial and int(lines[i][0]) <= dia_final:
					matches.append(lines[i])
		
		table.setRowCount(len(matches))
		table.setColumnCount(6)

		table.setHorizontalHeaderLabels(headerlabel_array)

		font = QFont()
		font.setFamily('Segoe UI Black')
		font.setPointSize(9)

		for i in range(6):
			table.horizontalHeaderItem(i).setFont(font)

		llista = []

		suma_bi_reb = 0
		suma_iva_reb = 0
		suma_total_reb = 0

		#display in the table
		for i in range(len(matches)):
			llista.append('')

			suma_bi_reb += matches[i][4]
			suma_total_reb += matches[i][6]

			for j in range(6):
					if j == 0:
						data = str(matches[i][0]).zfill(2) + '/' + str(matches[i][1]).zfill(2) + '/' + str(matches[i][2])
						item = QTableWidgetItem(data)
						item.setTextAlignment(Qt.AlignHCenter)
						table.setItem(i,j, item)
						j = 2

					elif j == 4:
						iva = matches[i][5] / 100
						iva_euros = round(iva * matches[i][4], 2)

						suma_iva_reb += iva_euros

						item = QTableWidgetItem(str(iva_euros))
						item.setTextAlignment(Qt.AlignHCenter)
						table.setItem(i,j, item)

					elif j == 5:
						item = QTableWidgetItem(str(matches[i][6]))
						item.setTextAlignment(Qt.AlignHCenter)
						table.setItem(i,j, item)

					else:
						item = QTableWidgetItem(str(matches[i][j+2]))
						item.setTextAlignment(Qt.AlignHCenter)
						table.setItem(i,j, item)

		table.setVerticalHeaderLabels(llista)

		header = table.horizontalHeader()   
		header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
		header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
		header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
		header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
		header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
		header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

		bi.setText(str(round(suma_bi_reb, 2)) + ' \u20ac')
		y.setText(str(round(suma_iva_reb, 2)) + ' \u20ac')
		total.setText(str(round(suma_total_reb, 2)) + ' \u20ac')

		return suma_bi_reb, suma_iva_reb, suma_total_reb


	def show_table(self):

		os.chdir(carpeta_data)
		if not os.path.exists('factures_rebudes.db') and not os.path.exists('factures_emeses.db'):
			QMessageBox.warning(self, 'Warning!', 'No existeix cap factura emesa o rebuda')

		elif os.path.exists('factures_rebudes.db') and not os.path.exists('factures_emeses.db'):
			QMessageBox.warning(self, 'Warning!', 'Només existeixen factures rebudes')
			
			self.factures_taula('factures_rebudes', ['DATA', 'ESTABLIMENT', 'BASE IMPONIBLE', 'IVA %', 'IVA \u20ac', 'TOTAL'], self.table_1, self.bi_tot_1, self.iva_tot_1, self.total_tot_1)

		elif os.path.exists('factures_emeses.db') and not os.path.exists('factures_rebudes.db'):
			QMessageBox.warning(self, 'Warning!', 'Només existeixen factures emeses')
			
			self.factures_taula('factures_emeses', ['DATA', 'NUM FACTURA', 'BASE IMPONIBLE', 'IVA %', 'IVA \u20ac', 'TOTAL'], self.table_2, self.bi_tot_2, self.iva_tot_2, self.total_tot_2)			

		else:

			suma_bi_reb, suma_iva_reb, suma_total_reb = self.factures_taula('factures_rebudes', ['DATA', 'ESTABLIMENT', 'BASE IMPONIBLE', 'IVA %', 'IVA \u20ac', 'TOTAL'], self.table_1, self.bi_tot_1, self.iva_tot_1, self.total_tot_1)
			suma_bi_eme, suma_iva_eme, suma_total_eme = self.factures_taula('factures_emeses', ['DATA', 'NUM FACTURA', 'BASE IMPONIBLE', 'IVA %', 'IVA \u20ac', 'TOTAL'], self.table_2, self.bi_tot_2, self.iva_tot_2, self.total_tot_2)

			#Calcular diferencies i beneficis

			diferencia_bi = suma_bi_eme - suma_bi_reb
			diferencia_iva = suma_iva_eme - suma_iva_reb
			diferencia_tot = suma_total_eme - suma_total_reb

			self.dif_bi.setText(str(round(diferencia_bi, 2)) + ' \u20ac')
			self.dif_iva.setText(str(round(diferencia_iva, 2)) + ' \u20ac')
			self.dif_tot.setText(str(round(diferencia_tot, 2)) + ' \u20ac')

			tableExists = check_table_exists('CompanyName', 'stock')

			if os.path.exists('CompanyName.db') and tableExists == True:
				lines = read_database('CompanyName', 'stock', 'REF', 'ASC')

				total_stock_price = 0
				for i in range(len(lines)):
					total_stock_price += lines[i][4]

				self.stock.setText(str(round(total_stock_price, 2)) + ' \u20ac')
				self.beneficis_stock.setText(str(round(diferencia_bi+total_stock_price, 2)) + ' \u20ac')

			else:
				self.beneficis_stock.setText(str(round(diferencia_bi, 2)) + ' \u20ac')

	def reinit_dialog(self):
		self.table_1.clearContents()
		self.table_2.clearContents()

		self.bi_tot_1.setText('0,0' + ' \u20ac')
		self.iva_tot_1.setText('0,0' + ' \u20ac')
		self.total_tot_1.setText('0,0' + ' \u20ac')

		self.bi_tot_2.setText('0,0' + ' \u20ac')
		self.iva_tot_2.setText('0,0' + ' \u20ac')
		self.total_tot_2.setText('0,0' + ' \u20ac')

		self.dif_bi.setText('0,0' + ' \u20ac')
		self.dif_iva.setText('0,0' + ' \u20ac')
		self.dif_tot.setText('0,0' + ' \u20ac')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()


#VENTES
class Facturacio_clients(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('Facturacio_clients.ui', self)

		self.seleccionar.clicked.connect(self.show_table)

		self.numclient.textChanged.connect(self.validar_num_client)
		self.result.textChanged.connect(self.change_color_result)
		self.total.textChanged.connect(self.change_color_total)
		self.percentatge_variacio.textChanged.connect(self.change_color_estadistiques)

		self.veure.clicked.connect(self.facturacio_client)

		self.veure_total.clicked.connect(self.show_total)

		self.estadistica.clicked.connect(self.show_statistics)

	def change_color_total(self):
		if self.total.text() != '':
			self.total.setStyleSheet('border: 1px solid orange;')

	def change_color_result(self):
		if self.result.text() != '':
			self.result.setStyleSheet('border: 1px solid orange;')

	def change_color_estadistiques(self):
		x = self.percentatge_variacio.text()

		if x != '':

			if float(x[0:len(x)-1]) < 0:
				self.percentatge_variacio.setStyleSheet('border: 1px solid red;')
				self.percentatge_fact.setStyleSheet('border: 1px solid red;')
				self.posicio.setStyleSheet('border: 1px solid red;')
			elif float(x[0:len(x)-1]) > 0:
				self.percentatge_variacio.setStyleSheet('border: 1px solid green;')
				self.percentatge_fact.setStyleSheet('border: 1px solid green;')
				self.posicio.setStyleSheet('border: 1px solid green;')

		
	def show_table(self):

		ano = self.any.value()
		mess = self.mes.value()
		ordre = self.order.currentText()

		os.chdir(carpeta_data)
		control = check_table_exists('facturacio_clients', str(ano))

		if control == True:
			if ordre == 'Número client ascendent':
				lines = read_database('facturacio_clients', str(ano), 'ref', 'ASC')
			elif ordre == 'Número client descendent':
				lines = read_database('facturacio_clients', str(ano), 'ref', 'DESC')
			elif ordre == 'Facturació mensual ascendent' :
				lines = read_database('facturacio_clients', str(ano), mesos_minus[mess-1], 'ASC')
			else:
				lines = read_database('facturacio_clients', str(ano), mesos_minus[mess-1], 'DESC')

			self.table.setRowCount(len(lines))
			self.table.setColumnCount(13)

			self.table.setHorizontalHeaderLabels(['CLIENT', 'GENER', 'FEBRER', 'MARÇ', 'ABRIL', 'MAIG', 'JUNY', 'JULIOL', 'AGOST', 'SETEMBRE', 'OCTUBRE', 'NOVEMBRE', 'DESEMBRE'])

			font = QFont()
			font.setFamily('Segoe UI Black')
			font.setPointSize(9)

			for i in range(13):
				self.table.horizontalHeaderItem(i).setFont(font)

			llista = []
			for i in range(len(lines)):
				llista.append(lines[i][0])
				for j in range(13):
					fact = float(lines[i][j])
					self.table.setItem(i,j, QTableWidgetItem(str(round(fact, 2))))

			self.table.setVerticalHeaderLabels(llista)

			for i in range(len(lines)):
				self.table.verticalHeaderItem(i).setFont(font)

		else:
			QMessageBox.warning(self, 'Warning!', 'Cap venta realitzada per l\'any seleccionat')


	def validar_num_client(self):

		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, num_client

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, num_client

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 


	def facturacio_client(self):
		mes = self.mes.value()
		ano = self.any.value()

		os.chdir(carpeta_data)
		control = check_table_exists('facturacio_clients', ano)

		if control == True:

			control, num_client = self.validar_num_client()

			if control == True:
				lines = select_from_database_general('facturacio_clients', ano, num_client, 'ref', 'ref', 'ASC')

				if len(lines) != 0:

					facturacio = round(lines[0][mes], 2)

					self.result.setText(str(facturacio) + '\u20ac')
					return facturacio
				else:
					QMessageBox.warning(self, 'Warning', 'Aquest client encara no ha realitzat cap compra!')
					return False

			else:
				QMessageBox.warning(self, 'Warning!', 'Dades incorrectes!', QMessageBox.Discard)
				return False
		else:
			QMessageBox.warning(self, 'Warning!', 'Cap venta realitzada per l\'any seleccionat')
			return False

	def show_total(self):
		os.chdir(carpeta_data)
		if os.path.exists('facturacio_total.db'):
			mes = self.mes.value()
			ano = self.any.value()

			lines = select_from_database_general('facturacio_total', 'data', ano, 'ref', 'ref', 'ASC')

			fact_total = round(lines[0][mes], 2)

			if len(lines) != 0:
				self.total.setText(str(fact_total) + '\u20ac')
				return fact_total

			else:
				QMessageBox.warning(self, 'Warning', 'Cap venta realitzada l\'any seleccionat!')
				return False

		else:
			QMessageBox.warning(self, 'Warning!', 'Cap venta realitzada l\'any seleccionat')
			return False

	def show_statistics(self):
		mes = self.mes.value()
		ano = self.any.value()

		fact_client = self.facturacio_client()
		total = self.show_total()

		if fact_client == False or total == False:
			pass
		else:
			#Percentatge de facturació del client respecte el total
			percent = round((float(fact_client)/float(total))*100, 2)
			self.percentatge_fact.setText(str(percent) + '%')

			#Variació respecte el mes anterior
			num_client = self.numclient.text()
			lines = select_from_database_general('facturacio_clients', ano, num_client, 'ref', 'ref', 'ASC')

			if mes != 1: #Si es gener no ho podem comparar amb el mes anterior del mateix any
				anterior = float(lines[0][mes-1])

				variacio = round((float(fact_client) - anterior)/float(fact_client) * 100, 2)

				self.percentatge_variacio.setText(str(variacio) + '%')

			else:
				self.percentatge_variacio.setText('NULL')

			#Posició ranking facturació
			lines = read_database('facturacio_clients', ano, mesos_minus[mes-1], 'DESC')
			position = 0

			for i in range(len(lines)):
				if lines[i][0] == num_client:
					position = i+1

			self.posicio.setText(str(position))

	def reinit_dialog(self):
		self.numclient.setText('')
		self.result.setText('')
		self.total.setText('')
		self.percentatge_fact.setText('')
		self.percentatge_variacio.setText('')
		self.posicio.setText('')

		self.any.setValue(2018)
		self.mes.setValue(1)

		self.table.clearContents()

		self.percentatge_variacio.setStyleSheet('')
		self.percentatge_fact.setStyleSheet('')
		self.posicio.setStyleSheet('')
		self.result.setStyleSheet('')
		self.numclient.setStyleSheet('')
		self.total.setStyleSheet('')

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Ranking_facturacio(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('RankingFacturacio.ui', self)

		self.seleccionar.clicked.connect(self.show_table)

	def show_table(self):
		ano = self.any.value()
		mes = self.mes.value()

		os.chdir(carpeta_data)
		if os.path.exists('facturacio_clients.db'):
			tableExists = check_table_exists('facturacio_clients', ano)

			if tableExists == True:
				lines = read_database('facturacio_clients', ano, mesos_minus[mes-1], 'DESC')

				self.table.setRowCount(len(lines))
				self.table.setColumnCount(10)

				self.table.setHorizontalHeaderLabels(['POSICIÓ', 'FACTURACIÓ', 'CLIENT', 'NOM COMERCIAL', 'NOM FISCAL', 'ADREÇA', 'POBLACIÓ', 'NIF', 'TEL', 'FORMA PAGO'])

				font = QFont()
				font.setFamily('Segoe UI Black')
				font.setPointSize(9)

				for i in range(10):
					self.table.horizontalHeaderItem(i).setFont(font)

				llista = []
				for i in range(len(lines)):
					llista.append('')

					dades_client = select_from_database_general('clients', 'data', lines[i][0], 'num_client', 'num_client', 'ASC')

					for j in range(10):
						if j == 0:
							self.table.setItem(i,j, QTableWidgetItem(str(i+1)))
						elif j == 1:
							self.table.setItem(i,j, QTableWidgetItem(str(lines[i][mes])))
						else:
							self.table.setItem(i,j, QTableWidgetItem(dades_client[0][j-2]))


				self.table.setVerticalHeaderLabels(llista)

				header = self.table.horizontalHeader()   
				for i in range(10):
					header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
			else:
				QMessageBox.warning(self, 'Warning', 'Cap venta realitzada l\'any seleccionat!')

		else:
			QMessageBox.warning(self, 'Warning', 'Cap venta realitzada!')

	def reinit_dialog(self):
		self.table.clearContents()	

				
	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()

class Grafics(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('Grafics.ui', self)

		self.numclient.textChanged.connect(self.validar_num_client)
		self.seleccionar.clicked.connect(self.veure_grafic)

	def validar_num_client(self):
		num_client = self.numclient.text()
		validar = re.match('^[0123456789]+$', num_client)

		if num_client == '': #Si esta buit bordes grocs								
			self.numclient.setStyleSheet('border: 1px solid yellow;')
			return False, 0

		elif not validar:#Si no es valid bordes vermells
			self.numclient.setStyleSheet('border: 1px solid red;')
			return False, 0

		else:
			self.numclient.setStyleSheet('border: 1px solid green;')
			return True, num_client 


	def fer_grafic_facturacio_total(self):
		os.chdir(carpeta_data)

		if os.path.exists('facturacio_total.db'):

			x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
			y = []		
			mesos = ['Gen', 'Feb', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ag', 'Set', 'Oct', 'Nov', 'Des']

			if self.comboBox.currentText() == 'Tots els anys':

				lines = read_database('facturacio_total', 'data', 'ref', 'ASC')
				plt.figure()

				for i in range(len(lines)):
					y.append(lines[i][1:])

				#Calcular mitja
				mitja = []

				for i in range(len(y)):
					suma = 0
					for j in range(len(y[i])):
						suma += y[i][j]

					mitja.append(suma/12)

				mitja_total = 0
				for i in range(len(mitja)):
					mitja_total += mitja[i]

				mitja_total = mitja_total/len(mitja)

				mitja_arr = np.linspace(mitja_total, mitja_total, 12)

				for i in range(len(lines)):
					plt.plot(x, y[i], '-o', label = lines[i][0])

				plt.plot(x, mitja_arr, '--', label = 'Mitjana total= %.2f \u20ac' % mitja_total)

				#Customize plot
				plt.title('Facturació total')
				plt.ylabel('Facturació \u20ac')
				plt.xticks(x, mesos)
				plt.legend()
				#plt.show()

				plt.savefig('facturacio_total.png')

				if self.refresh.isChecked():
					plt.gcf().clear()

			else:

				year = self.ano.value()

				lines = select_from_database_general('facturacio_total', 'data', str(year), 'ref', 'ref', 'ASC')

				if len(lines) == 0:
					QMessageBox.warning(self, 'Warning!', 'No existeix facturació per l\'any seleccionat')

				else:
					suma = 0
					zeros = 0
					for i in range(12):
						suma += float(lines[0][i])
						if float(lines[0][i]) == 0: zeros += 1

					mitja = suma/(12-zeros)

					mitja_arr = []
					for i in range(12):
						mitja_arr.append(mitja)

					plt.plot(x, lines[0][1:], '-o', label = lines[0][0])
					plt.plot(x, mitja_arr, '--', label='Mitjana %s: %.2f \u20ac' % (year, mitja))

					#Customize plot
					plt.title('Facturació total')
					plt.ylabel('Facturació \u20ac')
					plt.xticks(x, mesos)
					plt.legend()
					#plt.show()

					plt.savefig('facturacio_total.png')

					if self.refresh.isChecked():
						plt.gcf().clear()

		else:
			QMessageBox.warning(self, 'Warning!', 'No existeix facturació!')

	def fer_grafic_facturacio_clients(self):
		os.chdir(carpeta_data)

		if os.path.exists('facturacio_clients.db'):

			x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
			y = []		
			mesos = ['Gen', 'Feb', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ag', 'Set', 'Oct', 'Nov', 'Des']

			if self.seleccio_clients.currentText() == 'Tots els clients':

				year = self.spinBox_any.value()

				lines = read_database('facturacio_clients', str(year), 'ref', 'ASC')
				plt.figure(figsize=(8, 6))

				for i in range(len(lines)):
					y.append(lines[i][1:])

				#Calcular mitja
				mitja = []
				mitja_arr = []

				for i in range(len(y)):
					suma = 0
					for j in range(len(y[i])):
						suma += y[i][j]

					mitja.append(suma/12)

				mitja_total = 0
				for i in range(len(mitja)):
					mitja_total += mitja[i]

				for i in range(len(x)):
					mitja_arr.append(mitja_total/len(mitja))

				for i in range(len(lines)):
					plt.plot(x, y[i], '-o', label = lines[i][0])

				plt.plot(x, mitja_arr, '--', label = 'Mitjana total')
					
				#Customize plot
				plt.title('Facturació total')
				plt.ylabel('Facturació \u20ac')
				plt.xticks(x, mesos)
				plt.legend(loc='upper left')

				plt.savefig('facturacio_clients.png')

				if self.refresh.isChecked():
					plt.gcf().clear()

			else:
				year = self.spinBox_any.value()
				control, num_client = self.validar_num_client()

				control_2 = False
				if control == True:
					if check_table_exists('clients', 'data'):
						lines = select_from_database_general('clients', 'data', str(num_client).zfill(4), 'num_client', 'num_client', 'ASC')
						
						if len(lines) != 0:
							control_2 = True

						else:
							QMessageBox.warning(self, 'Warning!', 'Client no registrat!')
							control_2 = False 

					else:
						QMessageBox.warning(self, 'Warning!', 'Encara no has registrat cap client!')

				else:
					QMessageBox.warning(self, 'Warning!', 'Número de client no vàlid!')

				if control_2 == True:

					lines = select_from_database_general('facturacio_clients', str(year), str(num_client).zfill(4), 'ref', 'ref', 'ASC')

					if len(lines) != 0:

						suma = 0
						for i in range(len(x)):
							suma += float(lines[0][i])

						mitja = suma/12

						mitja_arr = []
						for i in range(len(x)):
							mitja_arr.append(mitja)

						plt.plot(x, lines[0][1:], '-o', label = lines[0][0])
						plt.plot(x, mitja_arr, '--', label='Mitjana %s' % num_client)

						#Customize plot
						plt.title('Facturació total')
						plt.ylabel('Facturació \u20ac')
						plt.xticks(x, mesos)
						plt.legend()

						plt.savefig('facturacio_clients.png')

						if self.refresh.isChecked():
							plt.gcf().clear()

					else:
						QMessageBox.warning(self, 'Warning!', 'Aquest client no ha facturat res!')

		else:
			QMessageBox.warning(self, 'Warning!', 'No existeix facturació!')

	def veure_grafic(self):
		os.chdir(carpeta_data)

		self.reinit_dialog()

		if self.checkBox.isChecked() and self.check_clients.isChecked():
			QMessageBox.warning(self, 'Warning!', 'Només pots seleccionar un dels dos gràfics!')

		elif self.checkBox.isChecked():
			self.fer_grafic_facturacio_total()
			filename = 'facturacio_total.png'
			image = QImage(filename)

			self.imageLabel.setPixmap(QPixmap.fromImage(image))


		elif self.check_clients.isChecked():
			self.fer_grafic_facturacio_clients()
			filename = 'facturacio_clients.png'
			image = QImage(filename)

			self.imageLabel.setPixmap(QPixmap.fromImage(image))

		else:
			QMessageBox.warning(self, 'Warning!', 'Has de marcar alguna de les dues opcions!')

			
	def reinit_dialog(self):
		os.chdir(carpeta_data)

		if os.path.exists('facturacio_total.png') and os.path.exists('facturacio_clients.png'):
			os.remove('facturacio_total.png')
			os.remove('facturacio_clients.png')

		elif os.path.exists('facturacio_total.png'):
			os.remove('facturacio_total.png')

		elif os.path.exists('facturacio_clients.png'):
			os.remove('facturacio_clients.png')

		self.imageLabel.clear()
		
		if self.refresh.isChecked():
			plt.gcf().clear()

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
			self.numclient.setText('')
			self.numclient.setStyleSheet('')
		else:
			event.ignore()

class Registre_ventes(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('RegistreVentes.ui', self)

		self.okbutton.clicked.connect(self.show_table)
		self.facturacio.textChanged.connect(self.canviar_color_fact)
		self.unitats.textChanged.connect(self.canviar_color_units)

	def canviar_color_fact(self):
		self.facturacio.setStyleSheet('border: 1px solid green;')
	def canviar_color_units(self):
		self.unitats.setStyleSheet('border: 1px solid green;')

	def show_table(self):
		month = self.mes.value()
		ano = self.any.value()

		os.chdir(carpeta_data)

		mes = mesos[int(month)-1]

		os.chdir(carpeta_data)
		control = check_table_exists('ventes', ano)
		control_2 = check_table_exists('facturacio_ref', ano)

		if control == False or control_2 == False:
			QMessageBox.warning(self, 'Warning!', 'No hi ha ventes realitzades aquest any!', QMessageBox.Discard)

		else:

			if self.comboBox_unitats.currentText() == 'Unitats ascendent':
				sales = read_database('ventes', str(ano), mesos_minus[month-1], 'ASC')

			elif self.comboBox_unitats.currentText() == 'Unitats descendent':
				sales = read_database('ventes', str(ano), mesos_minus[month-1], 'DESC')

			if self.comboBox_facturacio.currentText() == 'Facturació ascendent':
				lines = read_database('facturacio_ref', str(ano), mesos_minus[month-1], 'ASC')

			elif self.comboBox_facturacio.currentText() == 'Facturació descendent':
				lines = read_database('facturacio_ref', str(ano), mesos_minus[month-1], 'DESC')

			unitats_totals = 0
			facturacio_total = 0
			for i in range(len(sales)):
				unitats_totals += sales[i][month]

			for i in range(len(lines)):
				facturacio_total += lines[i][month]

			if len(sales) != 0 and len(lines) != 0:

				#Display the table
				self.table.setRowCount(len(sales))
				self.table.setColumnCount(13)
				self.table.setHorizontalHeaderLabels(['REF', 'GENER', 'FEBRER', 'MARÇ', 'ABRIL', 'MAIG', 'JUNY', 'JULIOL', 'AGOST', 'SETEMBRE', 'OCTUBRE', 'NOVEMBRE', 'DESEMBRE'])

				llista = []
				for i in range(len(sales)):
					llista.append(sales[i][0])
					for j in range(13):
						self.table.setItem(i,j, QTableWidgetItem(str(sales[i][j])))

				self.table.setVerticalHeaderLabels(llista)

				font = QFont()
				font.setFamily('Segoe UI Black')
				font.setPointSize(9)

				for i in range(13):
					self.table.horizontalHeaderItem(i).setFont(font)

				for i in range(len(sales)):
					self.table.verticalHeaderItem(i).setFont(font)

				#Display the table 2
				self.table_2.setRowCount(len(lines))
				self.table_2.setColumnCount(13)
				self.table_2.setHorizontalHeaderLabels(['REF', 'GENER', 'FEBRER', 'MARÇ', 'ABRIL', 'MAIG', 'JUNY', 'JULIOL', 'AGOST', 'SETEMBRE', 'OCTUBRE', 'NOVEMBRE', 'DESEMBRE'])

				llista = []
				for i in range(len(lines)):
					llista.append(lines[i][0])
					for j in range(13):
						self.table_2.setItem(i,j, QTableWidgetItem(str(lines[i][j])))

				self.table_2.setVerticalHeaderLabels(llista)

				for i in range(13):
					self.table_2.horizontalHeaderItem(i).setFont(font)

				for i in range(len(lines)):
					self.table_2.verticalHeaderItem(i).setFont(font)

				#Display facturacio total and unitats totals

				self.facturacio.setText(str(facturacio_total) + ' \u20ac')
				self.unitats.setText(str(unitats_totals) + ' u.')

			else:
				QMessageBox.warning(self, 'Warning!', 'No hi ha ventes realitzades aquest mes!', QMessageBox.Discard)

	def reinit_dialog(self):
		self.table.clearContents()
		self.table_2.clearContents()
		self.facturacio.setText('')
		self.unitats.setText('')

		self.facturacio.setStyleSheet('')
		self.unitats.setStyleSheet('')	
				
	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:
			event.accept()
			self.reinit_dialog()
		else:
			event.ignore()


#STOCK
class Stock(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		os.chdir(carpeta_data)
		uic.loadUi('Stock.ui', self)

		self.show_table()

		self.guardar.clicked.connect(self.save_stock)
		self.visualitzar.clicked.connect(self.show_table)

	def show_table(self):

		if os.path.exists('cataleg.db'):

			if self.order.currentText() == 'Referència ascendent':
				lines = read_database('cataleg', 'data', 'ref', 'ASC') #[ref, prod, preu]
			elif self.order.currentText() == 'Referència descendent':
				lines = read_database('cataleg', 'data', 'ref', 'DESC')
			elif self.order.currentText() == 'Alfabètic ascendent':
				lines = read_database('cataleg', 'data', 'prod', 'ASC')
			elif self.order.currentText() == 'Alfabètic descendent':
				lines = read_database('cataleg', 'data', 'prod', 'DESC')

			#Comprovar si hi ha o no stock existent
			tablas = [
						"""
							CREATE TABLE IF NOT EXISTS stock(
								REF TEXT NOT NULL,
								NAME TEXT NOT NULL,
								QUANTITY REAL NOT NULL,
								UNIT_PRICE REAL NOT NULL,
								TOTAL_PRICE REAL NOT NULL
							); 
						""" 
					]

			create_database('CompanyName', tablas)
			stock_lines = read_database('CompanyName', 'stock', 'REF', 'ASC')

			self.table.setRowCount(len(lines))
			self.table.setColumnCount(5)

			if len(stock_lines) == 0: #No previous stock

				llista = []
				for i in range(len(lines)):
					llista.append('')
					for j in range(5):
						if j == 0: #REF
							self.table.setItem(i,j, QTableWidgetItem(lines[i][0]))

						elif j == 1: #NAME
							self.table.setItem(i,j, QTableWidgetItem(lines[i][1]))

						elif j == 2: #QUANTITY
							sp = QSpinBox()
							sp.setMaximum(9999)
							self.table.setCellWidget(i,j, sp)

						elif j == 3: #UNIT PRICE
							self.table.setItem(i,j, QTableWidgetItem(str(lines[i][2])))

						elif j == 4: #TOTAL PRICE
							total_price = lines[i][2] * self.table.cellWidget(i,2).value()
							self.table.setItem(i,j, QTableWidgetItem(str(total_price)))

			else:

				llista = []
				for i in range(len(lines)):
					llista.append('')
					for j in range(5):
						if j == 0: #REF
							self.table.setItem(i,j, QTableWidgetItem(lines[i][0]))

						elif j == 1: #NAME
							self.table.setItem(i,j, QTableWidgetItem(lines[i][1]))

						elif j == 2: #QUANTITY

							item = select_from_database_general('CompanyName', 'stock', lines[i][0], 'REF', 'REF', 'ASC')

							if len(item) != 0:
								quantity = item[0][2]
							else:
								quantity = 0

							sp = QSpinBox()
							sp.setMaximum(9999)
							sp.setValue(quantity)
							self.table.setCellWidget(i,j, sp)

						elif j == 3: #UNIT PRICE
							self.table.setItem(i,j, QTableWidgetItem(str(lines[i][2])))

						elif j == 4: #TOTAL PRICE
							total_price = lines[i][2] * self.table.cellWidget(i,2).value()
							self.table.setItem(i,j, QTableWidgetItem(str(total_price)))

			self.table.setHorizontalHeaderLabels(['REF', 'PRODUCTE', 'QUANTITAT', 'PREU UNITAT', 'PREU TOTAL'])
			self.table.setVerticalHeaderLabels(llista)

			font = QFont()
			font.setFamily('Segoe UI Black')
			font.setPointSize(9)

			header = self.table.horizontalHeader()   

			for i in range(5):
				self.table.horizontalHeaderItem(i).setFont(font)
				header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

			header.setSectionResizeMode(1, QHeaderView.Stretch)

			#Stock total value

			tableExists = check_table_exists('CompanyName', 'stock')

			lines = read_database('CompanyName', 'stock', 'REF', 'ASC')

			total_stock_price = 0
			for i in range(len(lines)):
				total_stock_price += lines[i][4]

			self.stock.setText(str(round(total_stock_price, 2)) + ' \u20ac')

		else:
			QMessageBox.warning(self, 'Warning!', 'No existeix catàleg!')

	def save_stock(self):
		lines = self.table.rowCount()

		for i in range(lines):
			current_quantity = self.table.cellWidget(i,2).value()

			if current_quantity != 0:

				current_ref = self.table.item(i,0).text()
				current_name = self.table.item(i,1).text()
				current_unit_price = float(self.table.item(i,3).text())
				current_total_price = float(self.table.item(i,4).text())

				fill_table_stock('CompanyName', [current_ref, current_name, current_quantity, current_unit_price, current_total_price])

		QMessageBox.information(self, 'Information', 'Dades guardades correctament!')