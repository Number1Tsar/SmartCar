#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: panel_identification.py
Description: Identification Panel for Python SDK sample.
"""

import os
import uuid
import requests
import pyaudio
import wave
import wx
import wx.lib.scrolledpanel as scrolled
import azure.cognitiveservices.speech as speechsdk
import datetime

import util
import model
from view import base

import os
import cv2
# dir_path = os.path.dirname(os.path.realpath(__file__))
img_counter = 0



class IdentificationPanel(base.MyPanel):
    """Identification Panel."""

    def __init__(self, parent):
        super(IdentificationPanel, self).__init__(parent)

        self.large_person_group_id = str(uuid.uuid1())
        self.person_id_names = {}
        self.person_name_faces = {}
        self.faces = {}
        self.face_ids = []

        self.vsizer = wx.BoxSizer(wx.VERTICAL)

        self.panel = scrolled.ScrolledPanel(self)

        self.hsizer = wx.BoxSizer()
        self.hsizer.AddStretchSpacer()

        self.hvsizer = wx.BoxSizer(wx.VERTICAL)
        self.hvsizer.SetMinSize((util.INNER_PANEL_WIDTH, -1))

        label = ('1) Place face images of one person in a folder and give '
                 'the folder the same name as that person.\n'
                 '2) Repeat the step above one or more times, creating '
                 'different folders for different people.\n'
                 '3) Place all of the person folders in one root folder.\n'
                 '4) Click "Load Group" and select the root folder you '
                 'created above.\n'
                 '5) Click "Choose Image" to select a different image '
                 'representing one of the people for whom you created '
                 'folders above. The face in the image will be framed and '
                 'tagged with the name of the person.')
        self.static_text = wx.StaticText(self.panel, label=label)
        self.static_text.Wrap(util.INNER_PANEL_WIDTH)
        self.hvsizer.Add(self.static_text, 0, wx.ALL, 0)

        self.vhsizer = wx.BoxSizer()

        self.lsizer = wx.BoxSizer(wx.VERTICAL)
        self.lsizer.SetMinSize((util.MAX_IMAGE_SIZE, -1))

        flag = wx.EXPAND | wx.ALIGN_CENTER | wx.ALL
        self.btn_folder = wx.Button(self.panel, label='Load Group')
        self.lsizer.Add(self.btn_folder, 0, flag, 5)
        self.Bind(wx.EVT_BUTTON, self.OnChooseFolder, self.btn_folder)

        flag = wx.ALIGN_CENTER | wx.ALL | wx.EXPAND
        self.grid = base.CaptionWrapFaceList(self.panel)
        self.lsizer.Add(self.grid, 0, flag, 5)

        self.vhsizer.Add(self.lsizer, 1, wx.EXPAND)
        self.vhsizer.AddSpacer(90)

        self.rsizer = wx.BoxSizer(wx.VERTICAL)
        self.rsizer.SetMinSize((util.MAX_IMAGE_SIZE, -1))

        flag = wx.EXPAND | wx.ALIGN_CENTER | wx.ALL
        self.btn_file = wx.Button(self.panel, label='Capture Image')
        #btn_file = "Test.png"
        self.rsizer.Add(self.btn_file, 0, flag, 5)
        self.Bind(wx.EVT_BUTTON, self.OnChooseImage, self.btn_file)

        flag = wx.ALIGN_CENTER | wx.ALL
        self.bitmap = base.MyStaticBitmap(self.panel)
        self.rsizer.Add(self.bitmap, 0, flag, 5)

        self.vhsizer.Add(self.rsizer, 1, wx.EXPAND)

        self.hvsizer.Add(self.vhsizer)

        self.hsizer.Add(self.hvsizer)
        self.hsizer.AddStretchSpacer()
        self.hsizer.Layout()

        self.panel.SetSizer(self.hsizer)
        self.panel.Layout()
        self.panel.SetupScrolling(scroll_x=False)

        self.vsizer.Add(self.panel, 3, wx.EXPAND)

        self.log = base.MyLog(self)
        self.vsizer.Add(self.log, 1, wx.EXPAND)

        self.SetSizerAndFit(self.vsizer)

        self.btn_file.Disable()

    def OnChooseFolder(self, evt):
        """Choose Folder."""
        self.log.log((
            'Request: Group {0} will be used to build a person database. '
            'Checking whether the group exists.').format(
                self.large_person_group_id))
        try:
            util.CF.large_person_group.get(self.large_person_group_id)
            self.log.log(
                'Response: Group {0} exists.'.format(
                    self.large_person_group_id))
            text = ('Requires a clean up for group "{0}" before setting up a '
                    'new person database. Click YES to proceed, group "{0}" '
                    'will be cleared.').format(self.large_person_group_id)
            title = 'Warning'
            style = wx.YES_NO | wx.ICON_WARNING
            result = wx.MessageBox(text, title, style)
            if result == wx.YES:
                util.CF.large_person_group.delete(self.large_person_group_id)
                self.large_person_group_id = str(uuid.uuid1())
            else:
                return
        except util.CF.CognitiveFaceException as exp:
            if exp.code != 'LargePersonGroupNotFound':
                self.log.log('Response: {}. {}'.format(exp.code, exp.msg))
                return
            else:
                self.log.log(
                    'Response: Group {0} does not exist previously.'.format(
                        self.large_person_group_id))

        self.log.log(
            'Request: Creating group "{0}"'.format(self.large_person_group_id))
        util.CF.large_person_group.create(self.large_person_group_id)
        self.log.log('Response: Success. Group "{0}" created'.format(
            self.large_person_group_id))
        self.log.log((
            'Preparing faces for identification, detecting faces in chosen '
            'folder.'))

        dlg = wx.DirDialog(self)
        if dlg.ShowModal() != wx.ID_OK:
            return

        path = dlg.GetPath()

        self.person_id_names.clear()
        self.person_name_faces.clear()
        face_count = 0

        for person_name in os.listdir(path):
            path_person = os.path.join(path, person_name)
            if os.path.isdir(path_person):
                self.log.log(
                    'Request: Creating person "{0}"'.format(person_name))
                res = util.CF.large_person_group_person.create(
                    self.large_person_group_id, person_name)
                person_id = res['personId']
                self.log.log(
                    'Response: Success. Person "{0}" (PersonID: {1}) created'.
                    format(person_name, person_id))
                self.person_id_names[person_id] = person_name
                self.person_name_faces[person_name] = []
                for entry in os.listdir(path_person):
                    path_face = os.path.join(path_person, entry)
                    if os.path.isfile(path_face):
                        res = util.CF.large_person_group_person_face.add(
                            path_face, self.large_person_group_id, person_id)
                        if res.get('persistedFaceId'):
                            face_count += 1
                            face = model.Face(res, path_face)
                            self.person_name_faces[person_name].append(face)

        self.log.log('Response: Success. Total {0} faces are detected.'.
                     format(face_count))
        self.log.log(
            'Request: Training group "{0}"'.format(
                self.large_person_group_id))
        res = util.CF.large_person_group.train(self.large_person_group_id)

        self.grid.set_data(self.person_name_faces)
        self.panel.SetupScrolling(scroll_x=False)
        self.btn_file.Enable()

    def OnChooseImage(self, evt):
        """Choose Image."""
        start = datetime.datetime.now()
        util.CF.util.wait_for_large_person_group_training(
            self.large_person_group_id)
        self.log.log(
            'Response: Success. Group "{0}" training process is Succeeded'.
            format(self.large_person_group_id))

        # dlg = wx.FileDialog(self, wildcard=util.IMAGE_WILDCARD)
        # if dlg.ShowModal() != wx.ID_OK:
        #     return
        # path = dir_path + "/Test.JPG"
        path = self.snap_photo()
        self.bitmap.set_path(path)

        self.log.log('Detecting faces in {}'.format(path))
        self.faces.clear()
        del self.face_ids[:]

        res = util.CF.face.detect(path)
        for entry in res:
            face = model.Face(entry, path)
            self.faces[face.id] = face
            self.face_ids.append(face.id)

        self.log.log('Request: Identifying {0} face(s) in group "{1}"'.format(
            len(self.faces), self.large_person_group_id))
        res = util.CF.face.identify(
            self.face_ids,
            large_person_group_id=self.large_person_group_id)
        for entry in res:
            face_id = entry['faceId']
            if entry['candidates']:
                person_id = entry['candidates'][0]['personId']
                self.faces[face_id].set_name(self.person_id_names[person_id])
                end = datetime.datetime.now()
                print(end - start)
            else:
                self.faces[face_id].set_name('Unknown')
            nam = self.faces[face_id].name
            # print(nam)
            if("Sulav" == nam):
                print ("Sulav")
                self.play_audio("./ask_passphrase.wav")
                passphrase = self.read_voice()
                if(passphrase.lower() == "lock the car."):
                    r = requests.get('http://localhost:8000/unlock')
                    response = r.json()
                    self.play_audio("./unlocked.wav")
                    print(response)
                    break;
                elif(passphrase.lower() == "lock."):
                    r = requests.get('http://localhost:8000/lock')
                    response = r.json()
                    self.play_audio("./locked.wav")
                    print(response)
                else:
                    self.play_audio("./can't_recognize.wav")
                    print("passphrase wrong")
            else:
                self.play_audio("./can't_recognize.wav")

        util.draw_bitmap_rectangle(self.bitmap, self.faces.values())
        log_text = 'Response: Success.'
        for face_id in self.faces:
            log_text += ' Face {0} is identified as {1}.'.format(
                face_id, self.faces[face_id].name)
        self.log.log(log_text)


    def snap_photo(self):
        global img_counter
        cam = cv2.VideoCapture(0)
        # name = ""
        # dir_path = os.path.dirname(os.path.realpath(__file__))
        # if not os.path.exists(name):
        #     os.makedirs(name)
        # dir_path_new = os.chdir(dir_path + "\\" + name)
        ret, frame = cam.read()

        img_name = "opencv_frame_{}.png".format(img_counter)
        cv2.imwrite(img_name, frame)
        print("{} written!".format(img_name))
        img_counter += 1
        return "C:\\Smart\\Cognitive-Face-Python\\"+ img_name


    def read_voice(self):
        speech_key, service_region = "cc3653149fec41f0a7a999f1060a06d0", "westus"
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
        print("Say something...")
        result = speech_recognizer.recognize_once()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized: {}".format(result.text))
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(result.no_match_details))
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
        print("Result text "+result.text)
        return result.text

    def play_audio(self, file):
        chunk = 1024
        f = wave.open(file, "rb")
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(f.getsampwidth()),
                        channels=f.getnchannels(),
                        rate=f.getframerate(),
                        output=True)
        data = f.readframes(chunk)
        while data:
            stream.write(data)
            data = f.readframes(chunk)
        stream.stop_stream()
        stream.close()
        p.terminate()
