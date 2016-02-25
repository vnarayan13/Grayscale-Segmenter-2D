#execfile('<path to slicerSegmentationChecker.py>')

from __future__ import print_function
import slicer
import qt
import sys
import fnmatch
import time
import vtk
import pdb
import os

#LOAD Label Map in outline mode
#Open Editor for editing labels on the spot
#skip folders with underscore in them

class do_stuff:
  def __init__(self):
    realdir = ''
    logfilename = '' 

    ids = os.listdir(realdir) 

    for dir in ids:
      currdir = os.path.join(realdir, dir)
      listNodes = []  
      for root, dirs, filenames in os.walk(currdir):
        [listNodes.append(str(os.path.join(root,file))) for file in filenames]
        
      for node in listNodes:
        if 'masked' in node:
          segoutput = node
        elif 'original' in node:
          originalinput = node
        
      if not segoutput or not originalinput: 
        with open(logfilename,mode='a') as logfile: logfile.write("ERROR: missing segmentation or original node: " + dir + '\n')
        slicer.mrmlScene.Clear(0)
        continue
        
      segnode = slicer.util.loadVolume(segoutput, properties={"singleFile": True}, returnNode = True)
      originalnode = slicer.util.loadVolume(originalinput, properties={"singleFile": True}, returnNode = True)  

      if not segnode[0] or not originalnode[0]: 
        with open(logfilename,mode='a') as logfile: logfile.write("ERROR: images failed to load': " + dir + '\n')
        slicer.mrmlScene.Clear(0)
        continue
        
      # set display node for 
      appLogic = slicer.app.applicationLogic()
      selectionNode = appLogic.GetSelectionNode()
      selectionNode.SetReferenceActiveVolumeID(originalnode[1].GetID())
      selectionNode.SetReferenceSecondaryVolumeID(segnode[1].GetID())  
      appLogic.PropagateVolumeSelection()
      
      # stuff
      self.myRed = slicer.mrmlScene.GetNthNodeByClass(0,'vtkMRMLSliceCompositeNode') 
      self.myRed.SetForegroundOpacity(0.0)
      
      timer = qt.QTimer()
      timer.connect('timeout()',self.prit)
      timer.setInterval(50)
      
      line = None
      verdict = None
      self.interval = 0.05
      self.dire = '+'
      
      timer.start()
      while True:
        try:
          line = raw_input('>>> Enter verdict: ')
          if line=='1':
            break
          elif line=='0':
            break
          elif line=='exit':
            break   
        except KeyboardInterrupt:
          break        
      timer.stop()  
      if line=='exit':
        break  
      elif line=='1': 
        print(dir+': Passed')
        with open(logfilename,mode='a') as logfile: logfile.write("SUCCESS_id_" + dir + '\n')
        verdict = 1
        os.rename(currdir, currdir+'_passed')
      elif line=='0': 
        print(dir+': Failed')
        with open(logfilename,mode='a') as logfile: logfile.write("FAILED_id_" + dir + '\n')
        verdict = 0
        os.rename(currdir, currdir+'_failed')
      
      while line != 'y':
        line = raw_input('Confirm (y): ')
      
      print('\n') 
      slicer.mrmlScene.Clear(0)
      
  def prit(self):
    op = self.myRed.GetForegroundOpacity()
    if op > 0.80: self.dire = '-'
    elif op < 0.10: self.dire = '+'
    if self.dire == '+': self.myRed.SetForegroundOpacity(op+self.interval)
    elif self.dire == '-': self.myRed.SetForegroundOpacity(op-self.interval)

do_stuff()