#©Saul Needham

import socket
import threading
import tkinter as tk
from tkinter import *
from random import randint as rdi
from time import sleep as slp
from hashlib import sha256
import pyperclip
import queue

#-------------------------------------------------------------------------------

server = socket.socket()

host = '10.16.53.55' #IP address of server computer
port = 21212 #0  - 65535

server.connect((host, port))

qNotepad = queue.Queue()
qChat = queue.Queue()
qOutput = queue.Queue()

#queues to be used later when inserting text into widgets or onto canvas
#these are neccesary as you cannot insert straight from inside the receive loop

#-------------------------------------------------------------------------------

def receive():
    global privateKey, usernames, registered
    while True:
        try:
            message=server.recv(1024) #recieving message from server, not client
            dataString = message.decode("utf-8")
            dataString = dataString[1:-1].replace("'", "")  
            dataList = dataString.split(", ")
            #as socket cannot send lists, having to turn the stringed list back into a normal list data type

            normalTerms = ['LOGGEDIN','REGISTERED','USERNAMES','PUBLICKEY','ENCRYPTED','DECRYPTED','CHATSEND']
            #all message identifiers that could be sent by the server

            if dataList[0] == 'LOGGEDIN':
                #server will send once the user has a succesful login
                privKey = dataList[1]
                privKey = privKey.split('\\n')
                privKeyLines = ''
                for line in privKey:
                    privKeyLines += line+'\n'
                #will take the private key from the second index of the message and remove line breaks
                privKeyLines = privKeyLines[38:-38]
                #keyblocks are then cut off just leaving the numerical part of the key
                privKeyLines = privKeyLines[(keyLen+1):] #removing key identifier
                privateKey = privKeyLines[len(privKeyLines)::-1]
                #finally reverses the key so that it is compatible with the users public

            if dataList[0] == 'REGISTERED':
                qOutput.put('Account registered!')
                #as functions cannot be run in the threading function, we have to queue the message that is to be placed on the GUI
                registered = True
   
            if dataList[0] == 'USERNAMES':
                usernames = dataList.copy()
                usernames.pop(0)
            #copies the username list and deletes the message identifier 'USERNAMES'

            if dataList[0] == 'PUBLICKEY':
                #received back from server when the user copies a key on the notepad
                pubKey = dataList[1]
                pubKey = pubKey.split('\\n')
                pubKeyLines = ''
                for line in pubKey:
                    pubKeyLines += line+'\n'
                pubKeyLines = pubKeyLines[:-2]
                #line breaks are removed and replaced, and the unnecesary whitespace is cut off
                pyperclip.copy(pubKeyLines)
                #using pyperclip module to copy to clipboard

            if dataList[0] == 'ENCRYPTED':
                encryptedMessage = dataList[1]
                encryptedMessage = encryptedMessage.split('\\n')
                encryptedMessageLines = ''
                for line in encryptedMessage:
                    encryptedMessageLines += line+'\n'
                encryptedMessageLines = encryptedMessageLines[:-1]
                qNotepad.put(encryptedMessageLines)
            #encrypted message is recieved from server and then line breaks are removed
            #message is then put on a queue to be inserted onto GUI, as in threading loop
            
            if dataList[0] == 'DECRYPTED':
                decryptedMessage = dataList[1]
                qNotepad.put(decryptedMessage)
                #again message is put on a queue to be inserted onto GUI, as in threading loop

            if dataList[0] == 'CHATSEND':
                #receiving the chatlog from the server in following form:
                #['CHATSEND',user1,message1,user2,message2,user3,message3...]
                chatHistory = ''
                for i in range(len(dataList)-1):
                    if i%2==0: #even index so username
                        chatHistory+=(dataList[i+1]+':\n')
                    else: #odd index so message
                        chatHistory+=(dataList[i+1]+'\n')
                #username and messages built onto chatHistory string

                qChat.put(chatHistory)
                #then inserted into the global chat main widget
               
            if dataList[0] not in normalTerms:
                #single output messages to user
                qOutput.put(dataList[0])
                #these messages appear on the GUI dependant on the page
               
        except:
            #print('Error occured')
            #client.close()
            server.close()
            break

def queueNotepad():
    while True:
        try:
            message = qNotepad.get(block=False)
            #attempts to receieve a message from the queue
            textEntry.insert(tk.INSERT, message)
            #if succesful, the either encrypted or decyrpted message is place in text widget
        except queue.Empty:
            break
            #if no message is sent to the queue, the queue loop breaks
    root.after(50, queueNotepad)
    #resets the queue after 50ms which allows a short wait before resetting

def queueOutput(): #queue used for output messages on GUI
    while True:
        try:
            output = qOutput.get(block=False)
            coverLabel = tk.Label(root, text=' '*128) 
            #label of whitespace to cover up previous
            outputLabel = tk.Label(root, text=output)

            try: #attempting to place output message on the three possible widgets
                #login page in specific blank place
                loginCanvas.create_window(225, 190, window=coverLabel)
                loginCanvas.create_window(225, 190, window=outputLabel)
            except:
                try:
                    #register page in specific blank place
                    registerCanvas.create_window(225, 235, window=coverLabel)
                    registerCanvas.create_window(225, 235, window=outputLabel)
                except:
                    try:
                        #notepad in specific blank place
                        npCanvas.create_window(370, 100, window=coverLabel)
                        npCanvas.create_window(370, 100, window=outputLabel)
                    except:
                        pass
           
        except queue.Empty:
            break
        #again breaks the queue if no message is received
    root.after(50, queueOutput)
    #and queue is reset

def queueChat():
    while True:
        try:
            chat = qChat.get(block=False)
           
            chat = chat.split('\\n')
            chatLines = ''
            for line in chat:
                chatLines += line+'\n'
            chatLines = chatLines[:-2]

        #chatLog is placed in chat queue and then line breaks are removed

            try:
                #will attempt to place the chat into the widget if the user is on the global chat page
                chatLog.configure(state='normal') #makes widget editable
                chatLog.delete('1.0', END)
                chatLog.insert(tk.INSERT, chatLines)
                chatLog.configure(state='disabled') #re-makes widget read only
            except:
                pass
           
        except queue.Empty:
            break
    root.after(50, queueChat) #resets queue for next time a message is sent 

#--------------------------------------------------------------------------------

def loginPage():
    global loginCanvas, registerCanvas
    global usernameLogin, passwordLogin
    loginCanvas.destroy()  
    registerCanvas.destroy()
    #deleting other pages before creating new login page, so this becomes main
    loginCanvas = tk.Canvas(root, width = 450, height = 350)
    loginCanvas.pack()

    usernameLogin = tk.Entry(loginCanvas)
    usernameLogin.place(x = 210, y = 70, width=120, height=20)
    passwordLogin = tk.Entry(loginCanvas, show="*") 
    #makes it so everything typed in password box is replaced by stars '*'
    passwordLogin.place(x = 210, y = 110, width=120, height=20)

    label = tk.Label(root, text='Crypter') #main title label
    label.config(font=('Helvetica bold',28))
    loginCanvas.create_window(225, 30, window=label)
    label = tk.Label(root, text='Username:')
    loginCanvas.create_window(177,80, window=label)
    label = tk.Label(root, text='Password:')
    loginCanvas.create_window(177,120, window=label)
    label = tk.Label(root, text="Don't have an account?")
    loginCanvas.create_window(225,290, window=label)
    #adding specific text labels

    loginButton = tk.Button(text='Login', command=loginCheck)
    loginCanvas.create_window(225, 165, window=loginButton)

    switchToLButton = tk.Button(text='Go to register page', command=registerPage)
    loginCanvas.create_window(225, 320, window=switchToLButton)

    #two buttons (login and switch page) that will run specific functions from 'command='

#

def registerPage():
    global loginCanvas, registerCanvas
    global usernameRegister, passwordRegister1, passwordRegister2
    loginCanvas.destroy()
    registerCanvas.destroy()
    registerCanvas = tk.Canvas(root, width = 450, height = 350)
    registerCanvas.pack()
    #resetting page when switched to register page

    usernameRegister = tk.Entry(registerCanvas)
    usernameRegister.place(x = 210, y = 70, width=120, height=20)
    passwordRegister1 = tk.Entry(registerCanvas, show="*")
    passwordRegister1.place(x = 210, y = 110, width=120, height=20)
    passwordRegister2 = tk.Entry(registerCanvas, show="*") 
    #both pasword widgets replaced with stars '*'
    passwordRegister2.place(x = 210, y = 150, width=120, height=20)

    label = tk.Label(root, text='Crypter')
    label.config(font=('Helvetica bold',28))
    registerCanvas.create_window(225, 30, window=label)
    label = tk.Label(root, text='Username:')
    registerCanvas.create_window(177,80, window=label)
    label = tk.Label(root, text='Password:')
    registerCanvas.create_window(177,120, window=label)
    label = tk.Label(root, text='Confirm Password:')
    registerCanvas.create_window(155,160, window=label)
    label = tk.Label(root, text='Already have an account?')
    registerCanvas.create_window(225,290, window=label)

    loginButton = tk.Button(text='Register', command=registerCheck)
    registerCanvas.create_window(225, 205, window=loginButton)

    switchToLButton = tk.Button(text='Go to login page', command=loginPage)
    registerCanvas.create_window(225, 320, window=switchToLButton)
    #buttons again run specific functions from the command parameter

def loginCheck():
    global clientUsername
    password = passwordLogin.get()
    #takes entered password from widget on login page
    hashedPassword = sha256(password.encode('utf-8')).hexdigest()
    #then hashes the password through sha256
    dataList = ['login',
                usernameLogin.get(),
                hashedPassword]
    #data list is sent with message identifier 'login', along with the entered username and hashed password
    server.sendall(bytes(str(dataList), "utf-8"))
    slp(1)
    #delay for server to receive and check credentials
    if privateKey!='':
    #privateKey initially starts off blank, but is assigned the users key once the user logs in
    #this means that the login was succesful if privateKey is no longer blank
        clientUsername = usernameLogin.get()
        loginCanvas.destroy()
        notepadPage()
        #login page is destroyed and replaced by the notepad main UI

def registerCheck():
    password1 = passwordRegister1.get()
    hashedPassword1 = sha256(password1.encode('utf-8')).hexdigest()
    password2 = passwordRegister2.get()
    hashedPassword2 = sha256(password2.encode('utf-8')).hexdigest()
    #both passwords are hashed
    dataList = ['register',
                usernameRegister.get(),
                hashedPassword1,
                hashedPassword2]
    #and data list is sent containing message identifier 'register', username and passwords
    server.sendall(bytes(str(dataList), "utf-8"))
    slp(1)
    #short wait for server to receive and check credentials
    if registered == True:
        #once succesfully received a register code from server, register is set to True
        registerCanvas.destroy()
        loginPage()
        #and the user is redirected to the login page

#-------------------------------------------------------------------------------------

def notepadPage():
    global cCanvas, npCanvas
    global textEntry,publicEntry,userVar
   
    cCanvas.destroy()
    npCanvas.destroy()
    #resets other canvases as user could have switched page by button
    npCanvas = tk.Canvas(root, width = 450, height = 260)
    npCanvas.pack()
    #and re-creates notepad page

    textEntry = tk.Text(npCanvas)
    textEntry.place(x = 105, y = 112, width=335, height=66)
    publicEntry = tk.Text(npCanvas)
    publicEntry.place(x = 105, y = 22, width=335, height=66)
    #adds the public key and notepad text widgets to page

    notepadButton = tk.Button(text='Notepad',width=10,height=8)
    notepadButton.config(font=('Helvetica bold',10), fg='black', bg='grey') 
    #changing the colour of the button to grey so the user can see which page they are on
    npCanvas.create_window(45, 60, window=notepadButton)

    chatButton = tk.Button(text='Global Chat', command=chatPage, width=10, height=8)
    chatButton.config(font=('Helvetica bold',10), fg='black')
    npCanvas.create_window(45, 200, window=chatButton)

    #buttons to switch between the notepad and chat pages

    encryptButton = tk.Button(text='Encyrpt', command=encrypt, width=12, height=4)
    npCanvas.create_window(160, 220, window=encryptButton)

    decryptButton = tk.Button(text='Decrypt', command=decrypt, width=12, height=4)
    npCanvas.create_window(280, 220, window=decryptButton)

    copyButton = tk.Button(text='Copy public key', command=savePublicK, width=12, height=2)
    copyButton.config(bg='#BBBBBB')
    npCanvas.create_window(390, 205, window=copyButton)

    #buttons to encyrpt, decrypt and copy a users public key from the list

    userVar = StringVar(root)
    userVar.set(usernames[0])
    #making the dropdown list of usernames, with the front dropdown being the first username
   
    menuUsers= OptionMenu(root, userVar, *usernames)
    #adding the usernames list received from the server to the dropdown
    npCanvas.create_window(390, 245, window=menuUsers)

    labelKey = tk.Label(root, text='Public key:')
    npCanvas.create_window(133, 12, window=labelKey)
    labelNp = tk.Label(root, text='Notepad:')
    npCanvas.create_window(129, 100, window=labelNp)
   
def chatPage():
    global npCanvas, cCanvas
    global messageEntry,chatLog

    dataList = ['chatreq']
    server.sendall(bytes(str(dataList), "utf-8"))
    #every time the chat page is opened, the most up-to date chat log is requested
   
    cCanvas.destroy()
    npCanvas.destroy()
    cCanvas = tk.Canvas(root, width = 450, height = 260)
    cCanvas.pack()
    #replacing switched page to the new global chat page
 
    notepadButton = tk.Button(text='Notepad', command=notepadPage,width=10,height=8)
    notepadButton.config(font=('Helvetica bold',10), fg='black')
    cCanvas.create_window(45, 60, window=notepadButton)

    chatButton = tk.Button(text='Global Chat', width=10, height=8)
    chatButton.config(font=('Helvetica bold',10), fg='black', bg='grey')
    #changing the colour of the button to grey so the user can see which page they are on
    cCanvas.create_window(45, 200, window=chatButton)

    scrollbar = tk.Scrollbar(cCanvas)
    scrollbar.place(x=430, y=0, height=220)
    #making scroll bar for looking through chat log

    chatLog = tk.Text(cCanvas)
    chatLog.place(x=95, y=10, width=330, height=210)
    #making the chat log a text widget, which will later be made read only

    scrollbar.config(command=chatLog.yview)
    #binding the scrollbar to the chatLog text widget, to scroll vertically (yview)
 
    messageEntry = tk.Text(cCanvas)
    messageEntry.place(x = 100, y = 230, width=250, height=25)

    sendButton = tk.Button(text='Send', command=sendMessage, width=10, height=1)
    cCanvas.create_window(400, 242, window=sendButton)
    #button that will run function to send entered message

 
#-------------------------------------------------------------------------------

def encrypt():
    coverLabel = tk.Label(root, text=' '*128) 
    #label of whitespace to cover up previous message on UI
    npCanvas.create_window(370, 100, window=coverLabel)
   
    text=(textEntry.get("1.0",tk.END+"-1c")).lower()
    #takes the entered message and makes lower case
    publicKey=publicEntry.get("3.0",tk.END+"-36c")
    dataList = ['encrypt',
                text,
                publicKey]
    #data list containing 'encrypt' identifier, the decrypted message and the copied public key
    server.sendall(bytes(str(dataList), "utf-8"))
    textEntry.delete('1.0', END)
    #clear the message widget so it can be filled in with message once encrypted
 
#

def decrypt():
    coverLabel = tk.Label(root, text=' '*128) 
    #label of whitespace
    npCanvas.create_window(370, 100, window=coverLabel)

    text=textEntry.get("3.0",tk.END+"-28c")
    dataList = ['decrypt',
                text,
                privateKey]
    #data list containing 'decrypt' identifier, the encrypted message and their own private key
    server.sendall(bytes(str(dataList), "utf-8"))
    textEntry.delete('1.0', END)
    #clears message widget

#

def savePublicK():
    usernameP = userVar.get()
    dataList = ['keyreq',
                usernameP]
    #data list that will request the key of the username they selected from the list (usernameP)
    server.sendall(bytes(str(dataList), "utf-8"))

#

def sendMessage():
    message = messageEntry.get("1.0",tk.END)
    #takes message currently entered in the message widget
    if message.isspace() == False: #checks if message actually has content
        messageEntry.delete('1.0', END)
        #clears the message entry as your message has been sent, and user will see appear in global chat
        dataList = ['send',
                    clientUsername,
                    message]
        #send the users name, along with their message to update the chat
        server.sendall(bytes(str(dataList), "utf-8"))

#-------------------------------------------------------------------------------------------------------------------
   
root = tk.Tk()
root.title('Crypter')

root.iconbitmap("Crypter logo 1.ico")
#binds the logo to the root, to show on all pages of the UI

root.resizable(False, False) 
#makes it so the user cannot resize the window, fixing aspect ratio

root.after(50, queueNotepad)
root.after(50, queueChat)
root.after(50, queueOutput)
#starting the queues to allow them to be used

registerCanvas = tk.Canvas(root, width = 450, height = 350)
loginCanvas = tk.Canvas(root, width = 450, height = 350)
cCanvas = tk.Canvas(root, width = 450, height = 350)
npCanvas = tk.Canvas(root, width = 450, height = 350)
#creates all pages, and these are made global in their respective functions

privateKey='' #set for logging in user
registered = False #set for registering user
keyLen = 10

#-------------------------------------------------------------------------------------

receive_thread=threading.Thread(target=receive)
receive_thread.start()
#begins the receive thread to listen for messages from server 

loginPage()
#program starts by opening on login canvas

#-------------------------------------------------------------------------------------------------------------------

root.mainloop
#starts tkinter mainloop