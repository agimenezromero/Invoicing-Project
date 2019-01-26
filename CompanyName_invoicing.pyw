import sys, re
import PyQt5
from PyQt5.QtWidgets import QApplication, QLineEdit, QMainWindow, QMessageBox, QDialog, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView, QSpinBox, QDoubleSpinBox, QGraphicsView, QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, QDate, Qt
from PyQt5.QtGui import QIcon, QPixmap, QFont, QImage

import sqlite3
import os.path

from Invoicing_classes import *

dir_principal = os.getcwd()
carpeta_data = dir_principal + '\Data' #'C:\\Users\Alex Giménez Romero\Desktop\Distribucions Amilcar\Programa facturació\Clients'

os.chdir(dir_principal)
if not os.path.exists(carpeta_data): os.makedirs(carpeta_data)

class Window(QMainWindow): #Ventana principal
	"""docstring for Window"""
	def __init__(self):
		#Iniciar el objeto QMainWindow
		QMainWindow.__init__(self)
		#cargar la configuración del arxivo .ui en el objeto
		os.chdir(carpeta_data)
		uic.loadUi('MainWindow.ui', self)

		self.showMaximized()
		os.chdir(dir_principal)
 
		self.nou_client = Nou_client() #utilitzem la clase Nou_client amb la variable nou_client
		self.boto_nou_client.clicked.connect(self.obrir_nou_client) #Quan cliqui fara la funció obrir_nou_client definida mes a baix
		
		self.realitzar_factura = Factura()
		self.boto_factura.clicked.connect(self.obrir_realitzar_factura)

		self.substituir_factura = Substituir_factura()
		self.boto_substituir_factura.clicked.connect(self.obrir_substituir_factura)

		self.mostrar_cataleg = Cataleg()
		self.boto_cataleg.clicked.connect(self.obrir_cataleg)

		self.nou_producte = Nou_producte()
		self.boto_nou_producte.clicked.connect(self.obrir_nou_producte)

		self.mostrar_clients = Registre_clients()
		self.boto_registre_clients.clicked.connect(self.obrir_clients)

		self.buscar_clients = Buscar_client()
		self.boto_buscar_client.clicked.connect(self.obrir_buscar_clients)

		self.modificar_clients = Modificar_client()
		self.boto_modificar_client.clicked.connect(self.obrir_modificar_clients)

		self.registre_ventes = Registre_ventes()
		self.boto_registre_ventes.clicked.connect(self.obrir_registre_ventes)

		self.facturacio_clients = Facturacio_clients()
		self.boto_facturacio_clients.clicked.connect(self.obrir_facturacio_clients)

		self.ranking_facturacio = Ranking_facturacio()
		self.boto_ranking_facturacio.clicked.connect(self.obrir_ranking_facturacio)

		self.introduir_preu_producte = Introduir_preu_producte()
		self.boto_introduir_preu_producte.clicked.connect(self.obrir_introduir_preu_producte)

		self.veure_preus = Veure_preus()
		self.boto_veure_preus.clicked.connect(self.obrir_veure_preus)

		self.introduir_factures_rebudes = Introduir_factures_rebudes()
		self.boto_introduir_factura.clicked.connect(self.obrir_introduir_factures_rebudes)

		self.factures_rebudes = Factures_rebudes()
		self.boto_factures_rebudes.clicked.connect(self.obrir_factures_rebudes)

		self.factures_emeses = Factures_emeses()
		self.boto_factures_emeses.clicked.connect(self.obrir_factures_emeses)

		self.marge = Marge()
		self.boto_marge.clicked.connect(self.obrir_marge)

		self.abonos = Abonos()
		self.boto_abonos.clicked.connect(self.obrir_abonos)

		self.grafics = Grafics()
		self.boto_grafics.clicked.connect(self.obrir_grafics)

		self.stock = Stock()
		self.boto_stock.clicked.connect(self.obrir_stock)

		self.albaran = Albaran()
		self.boto_albaran.clicked.connect(self.obrir_albaran)

		self.factura_albaranes = Factura_albaranes()
		self.boto_factura_albaranes.clicked.connect(self.obrir_factura_albaranes)

		self.substituir_albaran = Substituir_albaran()
		self.boto_substituir_albaran.clicked.connect(self.obrir_substituir_albaran)

	def closeEvent(self, event):
		result = QMessageBox.question(self, 'Sortint...','Segur que vols sortir?', QMessageBox.Yes | QMessageBox.No)
		if result == QMessageBox.Yes:event.accept()
		else:event.ignore()

	def obrir_nou_client(self):
		self.nou_client.exec_()

	def obrir_cataleg(self):
		self.mostrar_cataleg.exec_()

	def obrir_nou_producte(self):
		self.nou_producte.exec_()

	def obrir_clients(self):
		self.mostrar_clients.exec_()

	def obrir_buscar_clients(self):
		self.buscar_clients.exec_()

	def obrir_modificar_clients(self):
		self.modificar_clients.exec_()

	def obrir_registre_ventes(self):
		self.registre_ventes.exec_()

	def obrir_realitzar_factura(self):
		self.realitzar_factura.exec_()

	def obrir_substituir_factura(self):
		self.substituir_factura.exec_()

	def obrir_facturacio_clients(self):
		self.facturacio_clients.exec_()

	def obrir_ranking_facturacio(self):
		self.ranking_facturacio.exec_()

	def obrir_introduir_preu_producte(self):
		self.introduir_preu_producte.exec_()

	def obrir_modificar_preu_producte(self):
		self.modificar_preu_producte.exec_()

	def obrir_veure_preus(self):
		self.veure_preus.exec_()

	def obrir_introduir_factures_rebudes(self):
		self.introduir_factures_rebudes.exec_()

	def obrir_factures_rebudes(self):
		self.factures_rebudes.exec_()

	def obrir_factures_emeses(self):
		self.factures_emeses.exec_()

	def obrir_marge(self):
		self.marge.exec_()

	def obrir_abonos(self):
		self.abonos.exec_()

	def obrir_grafics(self):
		self.grafics.exec_()

	def obrir_stock(self):
		self.stock.exec_()

	def obrir_albaran(self):
		self.albaran.exec_()

	def obrir_factura_albaranes(self): 
		self.factura_albaranes.exec_()

	def obrir_substituir_albaran(self):
		self.substituir_albaran.exec_()

#Instancia para iniciar una aplicación
app = QApplication(sys.argv)
#Create an object of the Window class
_window=Window()

#Show the window
_window.show()

#Execute the application
app.exec_()