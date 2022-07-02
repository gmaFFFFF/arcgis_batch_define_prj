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

def GetListMxdFile(parentFolder):
	'''
	Создает список, содержащий mxd-файлы
	'''
	listMxdFiles = []
	
	for dirname, dirnames, filenames in os.walk(parentFolder):
		for filename in filenames:
			if os.path.splitext(filename)[1].lower() == '.mxd': 
				fullName = os.path.join(dirname, filename).lower()
				listMxdFiles.append(fullName)		

	listMxdFiles.sort()
	
	return listMxdFiles

def GetDictDataFrame (listMxdFiles):
	'''
	Создает словарь в котором каждому mxd-файлу сопоставлены входящие в него фреймы данных
	'''	
	dictDataFrame = {}
	
	for mxdName in listMxdFiles:
		mxd = arcpy.mapping.MapDocument(mxdName)
		for df in arcpy.mapping.ListDataFrames(mxd):
			name = (mxdName,df.name.lower())
			dictDataFrame[name] = df.spatialReference.name.upper()
		del mxd
	
	return dictDataFrame

def GetDictDataFrameBySpatialReference (dictDataFrame):
	'''
	Возвращает словарь в котором каждой системе координат присовен список связанных с ней объектов
	'''
	dictDataFrameBySpatialReference = {}
	for o in dictDataFrame:
		currentSpatialRef = dictDataFrame[o]		
		if dictDataFrameBySpatialReference.get(currentSpatialRef):
			dictDataFrameBySpatialReference[currentSpatialRef].append(o)
		else:
			dictDataFrameBySpatialReference[currentSpatialRef] = [o,]
	
	return dictDataFrameBySpatialReference

def GetUsedSpatialReferences (dictDataFrameBySpatialReference):
	'''
	Возвращает множество, содержащее имена всех используемых пространствеными объектами систем координат
	'''
	setSpatialReferences = set()
	for spName in dictDataFrameBySpatialReference:
		setSpatialReferences.add(spName)
	
	return setSpatialReferences
		
def FilterDictDataFrameBySpatialRefNames(dictDataFrameBySpatialReference, listSpatialRefNameFilter):
	'''
	Фильтрует словарь, возвращая  объекты, у которых установлена проекция из списка listSpatialRefNameFilter
	'''
	listSpatialRefNameFilter = [name.upper() for name in listSpatialRefNameFilter]
	dictDataFrameBySpatialReferenceFiltered = {name:dictDataFrameBySpatialReference[name] for name in listSpatialRefNameFilter}
		
	return dictDataFrameBySpatialReferenceFiltered
	
def PrintDictDataFrameBySpatialReference (dictDataFrameBySpatialReference):
	'''
	Распечатывает систему координат и связанные с ней объекты
	'''
		
	for key in sorted(dictDataFrameBySpatialReference):
		printEnc('\n\t***  СК: %s  ***:\n'%key)
		printEnc('№ пп\tПространственный объект (Фрейм данных)')
		num = 1
		for df in dictDataFrameBySpatialReference[key]:
			printEnc ('%d.\t%s(%s)'%(num,df[0],df[1]))
			num += 1			

def BatchDefineProjection (dictDataFrame, prjfile, printLog = True):
	'''
	Осуществляет групповую установку системы координат
	'''	
	spatialRef = arcpy.SpatialReference(prjfile)	
	
	dictMxdDF = {}
	setMxdFile = {mxdName for mxdName,dfName in dictDataFrame}			
	for mxdName in setMxdFile:
		dfNames = [dfName for mxdNameS,dfName in dictDataFrame if mxdNameS == mxdName]
		dictMxdDF[mxdName] = dfNames
	
	for mxdName in setMxdFile:
		mxd = arcpy.mapping.MapDocument(mxdName)
		if printLog:
			printEnc ('Файл %s '%(mxd.filePath))
		dfs = [df for df in arcpy.mapping.ListDataFrames(mxd) if df.name.lower() in dictMxdDF[mxdName]]
		try:
			for df in dfs:				
				if printLog:
					printEnc ('-Установка проекции для фрейма данных %s ...'%(df.name))
				df.spatialReference = spatialRef								
			mxd.save()
			
		except Exception:
			printEnc('Файл %s обработать не удалось'%(mxd.filePath))
		
		
def BatchDefineProjectionRun ():
	'''
	Осуществляет групповую установку системы координат
	'''
	#Получаем исходные данные от пользователя
	printEnc('Введите путь к папке с файлами mxd:\n')
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
	listMxdFiles = GetListMxdFile(folder)
	dictDataFrame = GetDictDataFrame(listMxdFiles)
	dictDataFrameBySpatialReference = GetDictDataFrameBySpatialReference (dictDataFrame)
	
	printEnc('\nВ папке %s и её дочерних папках расположены следующие пространственные объекты:'%folder)
	PrintDictDataFrameBySpatialReference(dictDataFrameBySpatialReference)
	printEnc('---------------------------------------------------------------------')
	
	#Фильтруем объекты
	printEnc('\nВы можете отфильтровать фреймы данных, хранящиеся в mxd файлах, выбрав определенную систему координат. Выбор по имени фрейма или mxd файла не предусмотрен.')
	printEnc('Если Вы не хотите фильтровать фреймы данных, то введите 0.\n')
	
	usedSpatialReferences = sorted(list(GetUsedSpatialReferences (dictDataFrameBySpatialReference)))
	selectSpatialReferences = {0:'Все ниже перечисленные'}
	
	for num in range(1,len(usedSpatialReferences)+1):
		selectSpatialReferences[num] = usedSpatialReferences[num-1]
	
	printEnc('№\tНазвание')
	for num in sorted(selectSpatialReferences):
		printEnc ('%i\t%s'%(num,selectSpatialReferences[num]))
	
	
	printEnc('Введите номера систем координат (например: 3,5,9):')
	filterStr = inputEnc()
	filter = [int(n) for n in filterStr.split(',')]
	
	dictDataFrameBySpatialReferenceFiltered = dict()
	if 0 in filter:
		dictDataFrameBySpatialReferenceFiltered = FilterDictDataFrameBySpatialRefNames(dictDataFrameBySpatialReference, usedSpatialReferences)
	else:
		dictDataFrameBySpatialReferenceFiltered = FilterDictDataFrameBySpatialRefNames(dictDataFrameBySpatialReference, [usedSpatialReferences[n-1] for n in filter])
	
	#Меняем систему координат 
	printEnc('---------------------------------------------------------------------')
	printEnc('\nБудет осуществлена попытка изменить системы координат следующих фреймов данных:')	
	PrintDictDataFrameBySpatialReference(dictDataFrameBySpatialReferenceFiltered)
	
	spatialRef = arcpy.SpatialReference(prjfile)
	printEnc('\nВы действительно хотите установить систему координат %s для вышеуказанных фреймов данных? (Да/Нет/Yes/No)'%spatialRef.name)
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
	
	listDataFrameName = MergeListListsFunc(dictDataFrameBySpatialReferenceFiltered.values())
	dictDataFrameRedefine = {key:dictDataFrame[key] for key in dictDataFrame if key in listDataFrameName}
	
	BatchDefineProjection (dictDataFrameRedefine, prjfile)
	
	#Выявление объектов у которых не удалось установить проекцию 
	printEnc('Операция установки проекции завершена.')
	printEnc('---------------------------------------------------------------------')
	printEnc('\nПроверка результатов операции ...')
	printEnc('Операция может занять продолжительное время, подождите, пожалуйста ...\n')
	
	dictDataFrameBySpatialReferenceRes = {}
	
	#Этот фрагмент надо рефакторить с учетом GetDictDataFrameBySpatialReference()
	for mxdName,dfName in dictDataFrameRedefine:
		mxd = arcpy.mapping.MapDocument(mxdName)
		df = [df for df in arcpy.mapping.ListDataFrames(mxd) if df.name.lower() == dfName][0]
		currentSpatialRef = df.spatialReference.name.upper()
		if dictDataFrameBySpatialReferenceRes.get(currentSpatialRef):
			dictDataFrameBySpatialReferenceRes[currentSpatialRef].append((mxdName,dfName))
		else:
			dictDataFrameBySpatialReferenceRes[currentSpatialRef] = [(mxdName,dfName),]	
	#Конец рефакторинга
	
	usedSpatialReferencesRes = GetUsedSpatialReferences (dictDataFrameBySpatialReferenceRes)
	if spatialRef.name.upper() in usedSpatialReferencesRes:
		usedSpatialReferencesRes.remove(spatialRef.name.upper())
	
	if len(usedSpatialReferencesRes) == 0:
		printEnc('Установка проекции завершена успешно.')
	else:
		printEnc('---------------------------------------------------------------------')
		printEnc('\nНе удалось установить проекцию для следующих объектов:')
		dictDataFrameBySpatialReferenceResFiltered = FilterDictDataFrameBySpatialRefNames(dictDataFrameBySpatialReferenceRes, list(usedSpatialReferencesRes))
		PrintDictDataFrameBySpatialReference(dictDataFrameBySpatialReferenceResFiltered)
	
	printEnc('---------------------------------------------------------------------')

def main():
	
	#Информируем пользователя об осуществляемых действиях
	printEnc('''
*********************************************************************
\t   Групповая установка проекции mxd v 0.1
\tCopyright (C) 2017 Гришкин Максим (FFFFF@bk.ru)
\t\t\t(MIT License)
*********************************************************************
Назначение: Установка проекции для фреймов данных mxd файла 
в выбранной папке и ее подпапках.
Примечания:
 1.Вам потребуется указать папку с объектами, а также файл проекции, 
   который требуется применить.
 2.Вы сможете отфильтровать фреймы данных с учетом их системы координат.
 3.Для прерывания выполнения программы введите Ctrl+C. 
 4.Для работы скрипта требуется библиотека Esri ArcPy и лицензия. 
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