# coding: utf-8
'''
MIT License

Copyright © 2017 Гришкин Максим (FFFFF@bk.ru) 

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


Текст лицензии на русском языке.
Ограничение перевода: Это неофициальный перевод, 
он взят с сайта: http://licenseit.ru/wiki/index.php/MIT_License 
В случаях любого несоответствия перевода исходному тексту лицензии 
на английском языке верным считается текст на английском языке.

Copyright © 2017 Гришкин Максим (FFFFF@bk.ru) 
Данная лицензия разрешает, безвозмездно, лицам, получившим копию данного программного 
обеспечения и сопутствующей документации (в дальнейшем именуемыми "Программное Обеспечение"), 
использовать Программное Обеспечение без ограничений, включая неограниченное право 
на использование, копирование, изменение, объединение, публикацию, распространение, 
сублицензирование и/или продажу копий Программного Обеспечения, также как и лицам, 
которым предоставляется данное Программное Обеспечение, при соблюдении следующих условий:

Вышеупомянутый копирайт и данные условия должны быть включены во все копии 
или значимые части данного Программного Обеспечения.

ДАННОЕ ПРОГРАММНОЕ ОБЕСПЕЧЕНИЕ ПРЕДОСТАВЛЯЕТСЯ «КАК ЕСТЬ», БЕЗ ЛЮБОГО ВИДА ГАРАНТИЙ, 
ЯВНО ВЫРАЖЕННЫХ ИЛИ ПОДРАЗУМЕВАЕМЫХ, ВКЛЮЧАЯ, НО НЕ ОГРАНИЧИВАЯСЬ ГАРАНТИЯМИ ТОВАРНОЙ 
ПРИГОДНОСТИ, СООТВЕТСТВИЯ ПО ЕГО КОНКРЕТНОМУ НАЗНАЧЕНИЮ И НЕНАРУШЕНИЯ ПРАВ. 
НИ В КАКОМ СЛУЧАЕ АВТОРЫ ИЛИ ПРАВООБЛАДАТЕЛИ НЕ НЕСУТ ОТВЕТСТВЕННОСТИ 
ПО ИСКАМ О ВОЗМЕЩЕНИИ УЩЕРБА, УБЫТКОВ ИЛИ ДРУГИХ ТРЕБОВАНИЙ ПО ДЕЙСТВУЮЩИМ КОНТРАКТАМ, 
ДЕЛИКТАМ ИЛИ ИНОМУ, ВОЗНИКШИМ ИЗ, ИМЕЮЩИМ ПРИЧИНОЙ ИЛИ СВЯЗАННЫМ С ПРОГРАММНЫМ 
ОБЕСПЕЧЕНИЕМ ИЛИ ИСПОЛЬЗОВАНИЕМ ПРОГРАММНОГО ОБЕСПЕЧЕНИЯ 
ИЛИ ИНЫМИ ДЕЙСТВИЯМИ С ПРОГРАММНЫМ ОБЕСПЕЧЕНИЕМ.
'''

from __future__ import print_function, unicode_literals, absolute_import
import arcpy
import os
import locale

from arcpy import env
from arcpy.sa import *

def printEnc(s):
	print(s.encode(locale.getpreferredencoding()))
def inputEnc():
	return raw_input().decode(sys.stdin.encoding)

def GetListFolders(parentFolder):
	'''
	Создает список, содержащий текущий каталог, а также 
	все каталоги вложенные в него
	'''
	folders = [parentFolder,]
	
	for dirname, dirnames, filenames in os.walk(parentFolder):
		for subdirname in dirnames:
			subfolder = os.path.join(dirname, subdirname)
			folders.append (subfolder)
	
	return folders

def GetListSpatialObj (listFolders):
	'''
	Создает список, содержащий растры, shape-файлы, 
	пространственные объекты (за исключением объектов включенных в набор объектов) и наборы объектов из БГД
	Внимание: не включаются покрытия (Coverage)! Причина субъективная : я не знаю как работать с покрытиями (Coverage)
	'''
	listSpatialObj = []
	
	for folder in listFolders:
		
		# Растры
		env.workspace = folder
	
		for raster in arcpy.ListRasters():
			listSpatialObj.append(os.path.join(folder,raster))
		
		# Shape файлы
		env.workspace = folder
		
		for feature in arcpy.ListFeatureClasses():
			listSpatialObj.append(os.path.join(folder,feature))
					
			
		# Внутри БГД
		env.workspace = folder
		gdbs = arcpy.ListWorkspaces("*", "FileGDB")
		gdbs.extend(arcpy.ListWorkspaces("*", "Access"))
		gdbs.extend(arcpy.ListWorkspaces("*", "SDE"))
				
		for gdb in gdbs:
			arcpy.env.workspace = gdb
			# Набор данных
			for feature in arcpy.ListFeatureClasses():
				listSpatialObj.append(os.path.join(gdb,feature))
			# Класс пространственных объектов в БГД
			for dataset in arcpy.ListDatasets():
				listSpatialObj.append(os.path.join(gdb,dataset))
				
	listSpatialObj.sort()
	
	return listSpatialObj

def GetDictFeatureBySpatialReference (listSpatialObj):
	'''
	Возвращает словарь в котором каждой системе координат присовен список связанных с ней объектов
	'''
	dictSpatialRefFeatures = {}
	for o in listSpatialObj:	
		try:			
			#Получаем название системы координат текущего объекта		
			currentSpatialRef = arcpy.Describe(o).spatialReference.name.upper()
		except Exception:
			printEnc('Неизвестная ошибка! Невозможно обработать объект %s'%o)
			continue
		if dictSpatialRefFeatures.get(currentSpatialRef):
			dictSpatialRefFeatures[currentSpatialRef].append(o)
		else:
			dictSpatialRefFeatures[currentSpatialRef] = [o,]
	
	return dictSpatialRefFeatures

def GetUsedSpatialReferences (dictSpatialRefFeatures):
	'''
	Возвращает множество, содержащее имена всех используемых пространствеными объектами систем координат
	'''
	setSpatialReferences = set()
	for spName in dictSpatialRefFeatures:
		setSpatialReferences.add(spName)
	
	return setSpatialReferences
		
def FilterFeatureBySpatialRefNames(dictSpatialRefFeatures, listSpatialRefNameFilter):
	'''
	Фильтрует словарь, возвращая  объекты, у которых установлена проекция из списка listSpatialRefNameFilter
	'''
	listSpatialRefNameFilter = [name.upper() for name in listSpatialRefNameFilter]
	dictSpatialRefFeaturesFiltered = {name:dictSpatialRefFeatures[name] for name in listSpatialRefNameFilter}
		
	return dictSpatialRefFeaturesFiltered
	
def PrintFeatureBySpatialReference (dictSpatialRefFeatures):
	'''
	Распечатывает систему координат и связанные с ней объекты
	'''
		
	for key in sorted(dictSpatialRefFeatures):
		printEnc('\n\t***  СК: %s  ***:\n'%key)
		printEnc('№ пп\tПространственный объект')
		num = 1
		for feature in dictSpatialRefFeatures[key]:
			printEnc ('%d.\t%s'%(num,feature))
			num += 1			

def BatchDefineProjection (listSpatialObj, prjfile, printLog = True):
	'''
	Осуществляет групповую установку системы координат
	'''	
	for feature in listSpatialObj:
		if printLog:
			printEnc ('Установка проекции для %s ...'%feature)
		try:
			arcpy.DefineProjection_management(feature, prjfile)
		except Exception:
			e = sys.exc_info()[1]
			printEnc(e.args[0].decode('utf-8'))
			
def BatchDefineProjectionRun ():
	'''
	Осуществляет групповую установку системы координат
	'''
	#Получаем исходные данные от пользователя
	printEnc('Введите путь к папке с пространствеными объектами:\n')
	folder = inputEnc()
	
	while not (os.path.exists(folder) and os.path.isdir(folder)):
		printEnc('Указанная папка "%s" не существует, попробуйте еще раз:\n'%folder)
		folder = inputEnc()
	
	printEnc('Введите путь к файлу с описанием проекции (*.prj):\n')
	prjfile = inputEnc()
	
	while not (os.path.exists(prjfile) and os.path.isfile(prjfile)):
		printEnc('Указанный файл "%s" не существует, попробуйте еще раз:\n'%prjfile)
		prjfile = inputEnc()

	
	#Формируем список пространственных объектов		
	printEnc('---------------------------------------------------------------------')
	printEnc('\nОсуществляется поиск объектов.')
	printEnc('Операция может занять продолжительное время, пожалуйста, подождите ...')
	listFolders = GetListFolders (folder)
	listSpatialObj = GetListSpatialObj(listFolders)
	dictFeatureBySpatialReference = GetDictFeatureBySpatialReference (listSpatialObj)
	
	printEnc('\nВ папке %s и её дочерних папках расположены следующие пространственные объекты:'%folder)
	PrintFeatureBySpatialReference(dictFeatureBySpatialReference)
	printEnc('---------------------------------------------------------------------')
	
	#Фильтруем объекты
	printEnc('\nВы можете отфильтровать пространственные объекты выбрав объекты с определенной системой координат. Выбор по имени пространственного объекта не предусмотрен.')
	printEnc('Если Вы не хотите фильтровать пространственные объекты, то введите 0.\n')
	
	usedSpatialReferences = sorted(list(GetUsedSpatialReferences (dictFeatureBySpatialReference)))
	selectSpatialReferences = {0:'Все ниже перечисленные'}
	
	for num in range(1,len(usedSpatialReferences)+1):
		selectSpatialReferences[num] = usedSpatialReferences[num-1]
	
	printEnc('№\tНазвание')
	for num in sorted(selectSpatialReferences):
		printEnc ('%i\t%s'%(num,selectSpatialReferences[num]))
	
	
	printEnc('Введите номера систем координат (например: 3,5,9):')
	filterStr = inputEnc()
	filter = [int(n) for n in filterStr.split(',')]
	
	dictSpatialRefFeaturesFiltered = dict()
	if 0 in filter:
		dictSpatialRefFeaturesFiltered = FilterFeatureBySpatialRefNames(dictFeatureBySpatialReference, usedSpatialReferences)
	else:
		dictSpatialRefFeaturesFiltered = FilterFeatureBySpatialRefNames(dictFeatureBySpatialReference, [usedSpatialReferences[n-1] for n in filter])
	
	#Меняем систему координат 
	printEnc('---------------------------------------------------------------------')
	printEnc('\nБудет осуществлена попытка изменить системы координат следующих объектов:')	
	PrintFeatureBySpatialReference(dictSpatialRefFeaturesFiltered)
	
	spatialRef = arcpy.SpatialReference(prjfile)
	printEnc('\nВы действительно хотите установить систему координат %s для вышеуказанных объектов? (Да/Нет/Yes/No)'%spatialRef.name)
	answer = inputEnc()
	if answer[0] not in ('Д', 'д', 'Y', 'y'):
		printEnc('Работа программы завершена.')
		return
	
	printEnc('---------------------------------------------------------------------')
	printEnc('Осуществляется попытка установки проекции.')
	printEnc('Операция может занять продолжительное время, подождите, пожалуйста ...\n')
	
	#Функция, осуществляющая слияние списка списков
	MergeListListsFunc = lambda lls: reduce(lambda l,lnext: l.extend(lnext) or l, 
											lls, 
											[])
	
	listRedefineFeatures = MergeListListsFunc(dictSpatialRefFeaturesFiltered.values())

	BatchDefineProjection (listRedefineFeatures, prjfile)
	
	#Выявление объектов у которых не удалось установить проекцию 
	printEnc('Операция установки проекции завершена.')
	printEnc('---------------------------------------------------------------------')
	printEnc('\nПроверка результатов операции ...')
	printEnc('Операция может занять продолжительное время, подождите, пожалуйста ...\n')
	
	dictFeatureBySpatialReferenceRes = GetDictFeatureBySpatialReference (listRedefineFeatures)
	usedSpatialReferencesRes = GetUsedSpatialReferences (dictFeatureBySpatialReferenceRes)
	if spatialRef.name.upper() in usedSpatialReferencesRes:
		usedSpatialReferencesRes.remove(spatialRef.name.upper())
	
	if len(usedSpatialReferencesRes) == 0:
		printEnc('Установка проекции завершена успешно.')
	else:
		printEnc('---------------------------------------------------------------------')
		printEnc('\nНе удалось установить проекцию для следующих объектов:')
		dictFeatureBySpatialReferenceResFiltered = FilterFeatureBySpatialRefNames(dictFeatureBySpatialReferenceRes, list(usedSpatialReferencesRes))
		PrintFeatureBySpatialReference(dictFeatureBySpatialReferenceResFiltered)
	
	printEnc('---------------------------------------------------------------------')

def main():
	
	#Информируем пользователя об осуществляемых действиях
	printEnc('''
*********************************************************************
    Групповая установка проекции пространственных объектов v 0.1
\tCopyright (C) 2017 Гришкин Максим (FFFFF@bk.ru)
\t\t\t(MIT License)
*********************************************************************
Назначение: Установка проекции для объектов в папке и подпапках.
Примечания:
 1. Переопределение проекции затрагивает: 
\t-растры, 
\t-shape-файлы, 
\t-пространственные объекты и наборы объектов из БГД, 
\t кроме покрытий (Coverage).
 2.Вам потребуется указать папку с объектами, а также файл проекции, 
   который требуется применить.
 3.Данные не перепроецируются, осуществляется только перезапись 
   информации о проекции.
 4.Вы сможете отфильтровать пространственные объекты с учетом их 
   системы координат.
 5.Для прерывания выполнения программы введите Ctrl+C. 
 6.Для работы скрипта требуется библиотека Esri ArcPy и лицензия. 
*********************************************************************
''')
	
	stop = False
	
	while not stop:	
		BatchDefineProjectionRun ()
		printEnc('\nВы Хотите запустить еще один сеанс? (Да/Нет/Yes/No)')
		answer = inputEnc()
		if answer[0] not in ('Д', 'д', 'Y', 'y'):
			stop = True
		printEnc('---------------------------------------------------------------------\n\n')
	

main()