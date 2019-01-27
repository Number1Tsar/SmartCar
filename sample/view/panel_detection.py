#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: panel_detection.py
Description: Detection Panel for Python SDK sample.
"""

import wx
import time
import util
import model
from datetime import datetime
from view import base
import cv2
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
cam = cv2.VideoCapture(0)
faces_num = 0

img_counter = 0


class DetectionPanel(base.MyPanel):
    """Detection Panel."""

    def __init__(self, parent):
        super(DetectionPanel, self).__init__(parent)

        self.vsizer = wx.BoxSizer(wx.VERTICAL)

        self.hsizer = wx.BoxSizer()
        self.hsizer.AddStretchSpacer()

        self.hvsizer = wx.BoxSizer(wx.VERTICAL)
        self.hvsizer.SetMinSize((util.INNER_PANEL_WIDTH, -1))

        label = ("To detect faces in an image, click the 'Choose Image' "
                 "button. You will see a rectangle surrounding every face "
                 "that the Face API detects. You will also see a list of "
                 "attributes related to the faces.")
        self.static_text = wx.StaticText(self, label=label)
        self.static_text.Wrap(util.INNER_PANEL_WIDTH)
        self.hvsizer.Add(self.static_text, 0, wx.ALL, 5)

        self.vhsizer = wx.BoxSizer()
        self.vhsizer.SetMinSize((util.INNER_PANEL_WIDTH, -1))

        self.lsizer = wx.BoxSizer(wx.VERTICAL)
        self.lsizer.SetMinSize((util.MAX_IMAGE_SIZE, -1))

        flag = wx.EXPAND | wx.ALIGN_CENTER | wx.ALL
        self.btn = wx.Button(self, label='Take Image')
        self.lsizer.Add(self.btn, 0, flag, 5)
        self.Bind(wx.EVT_BUTTON, self.OnChooseImage, self.btn)

        flag = wx.ALIGN_CENTER | wx.ALL
        self.bitmap = base.MyStaticBitmap(self)
        self.lsizer.Add(self.bitmap, 0, flag, 5)

        self.vhsizer.Add(self.lsizer, 0, wx.ALIGN_LEFT)
        self.vhsizer.AddStretchSpacer()

        self.rsizer = wx.BoxSizer(wx.VERTICAL)
        self.rsizer.SetMinSize((util.MAX_IMAGE_SIZE, -1))

        style = wx.ALIGN_CENTER
        flag = wx.ALIGN_CENTER | wx.EXPAND | wx.ALL
        self.result = wx.StaticText(self, style=style)
        self.rsizer.Add(self.result, 0, flag, 5)

        flag = wx.ALIGN_LEFT | wx.EXPAND | wx.ALL
        self.face_list = base.MyFaceList(self)
        self.rsizer.Add(self.face_list, 1, flag, 5)

        self.vhsizer.Add(self.rsizer, 0, wx.EXPAND)

        self.hvsizer.Add(self.vhsizer)

        self.hsizer.Add(self.hvsizer, 0)
        self.hsizer.AddStretchSpacer()

        self.vsizer.Add(self.hsizer, 3, wx.EXPAND)

        self.log = base.MyLog(self)
        self.vsizer.Add(self.log, 1, wx.EXPAND)

        self.SetSizerAndFit(self.vsizer)

    def OnChooseImage(self, evt):
        """Take Image."""
        # dlg = wx.FileDialog(self, wildcard=util.IMAGE_WILDCARD)
        # if dlg.ShowModal() != wx.ID_OK:
        #     return
        # path = dlg.GetPath()
        # self.bitmap.set_path(path)
        # self.async_detect(path)
        start = datetime.now()
        face_detected = 0
        img_counter = 0
        dir_path = os.path.dirname(os.path.realpath(__file__))
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        cv2.imshow("Snap Photo", frame)
        name=input("Enter person name:")
        if not os.path.exists(name):
            os.makedirs(name)
        dir_path_new = dir_path+"\database\\"+name
        os.chdir(dir_path_new)
        cv2.namedWindow("Snap Photo")
        print(dir_path_new)
        end = datetime.now()
        while(face_detected != 1):
            # print("Taking snaps for authentication database, minimum 5 photos(prefrebly in diiferent poses, light condition, with/without glasses\n")
            # print("!!! Press Spacebar to photos!!!")
            img_name = "temp_frame_{}.png".format(img_counter)
            path = dir_path+"\\"+img_name
            cv2.imwrite(img_name, frame)
            print("{} written!".format(img_name))
            # time.sleep(1);
            print(path)
            end = datetime.now()
            diff = end - start
            print(diff.total_seconds())
            if(diff.total_seconds() >= 10 ):
                print("Called async_detect")
                face_detected = self.async_detect(path)
                start = datetime.now()
            if(face_detected == None):
                print("No face detected")
            print(face_detected)
            # time.sleep(1);
            print("faces", faces_num)
            if(face_detected == 1):
                img_counter += 1
                print("Image counter", img_counter )
                break
            elif (faces_num > 0):
                img_counter += 1
                print("Image counter", img_counter )
                break
            else:
                # os.remove(img_name)
                print("Image removed\n")
                # time.sleep(30)
            ret, frame = cam.read()
            cv2.imshow("Snap Photo", frame)
            if not ret:
                break


    @util.async
    def async_detect(self, path):
        """Async detection."""
        # self.log.log('Request: Detecting {}'.format(path))
        # self.result.SetLabelText('Detecting ...')
        # self.btn.Disable()
        # self.face_list.Clear()
        # self.face_list.Refresh()
        # self.rsizer.Layout()
        # self.vhsizer.Layout()
        print("Entered async_detect")
        try:
            attributes = (
                'age')##,gender,headPose,smile,facialHair,glasses,emotion,hair,'
                ##'makeup,occlusion,accessories,blur,exposure,noise')
            res = util.CF.face.detect(path, False, False, attributes)
            faces = [model.Face(face, path) for face in res]
            self.face_list.SetItems(faces)
            # util.draw_bitmap_rectangle(self.bitmap, faces)

            # log_text = 'Response: Success. Detected {} face(s) in {}'.format(
            #     len(res), path)
            # self.log.log(log_text)
            # text = '{} face(s) has been detected.'.format(len(res))
            # self.result.SetLabelText(text)
            faces_num = len(res)
            print("Try block")
        except util.CF.CognitiveFaceException as exp:
            # self.log.log('Response: {}. {}'.format(exp.code, exp.msg))
            print("Exception")
            # return -1

        # self.btn.Enable()
        # self.rsizer.Layout()
        # # self.vhsizer.Layout()
        # print("Returned ", len(res))

