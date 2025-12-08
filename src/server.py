#©Saul Needham

import threading
import socket
from time import sleep as slp
from random import randint as rdi

#-----------------------------------------------------------------

clients = []
usernames = []

host = socket.gethostbyname(socket.gethostname())
#gets current IP address of computer
port = 21212 #0  - 65535

server = socket.socket()

server.bind((host, port))
#and runs server on own IP and custom port number
server.listen()
#begins waiting for connections

#-----------------------------------------------------------------

KEYBLOCKLEN = 38
MESSAGELEN = 29
#constants that will later be used for key block splitting
keyLen = 10
PGPlen = keyLen+246
#total key length is 256 (246+starter key length of 10)
emptyPassword = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
#'' hashed through sha256

fillList=['a', 'b', 'c', 'd', 'e', 'f',
          'g', 'h', 'i', 'j', 'k', 'l',
          'm', 'n', 'o', 'p', 'q', 'r',
          's', 't', 'u', 'v', 'w', 'x',
          'y', 'z', 'A', 'B', 'C', 'D',
          'E', 'F', 'G', 'H', 'I', 'J',
          'K', 'L', 'M', 'N', 'O', 'P',
          'Q', 'R', 'S', 'T', 'U', 'V',
          'W', 'X', 'Y', 'Z', '=', '+',
          ',', '.', '?', '@', '~', '_',
          '(', ')', '[', ']', '{', '}',
          '/', ' ', '1', '2', '3', '4',
          '5', '6', '7', '8', '9', '0']
#random characters to be placed in encrypted messages
shift="abcdefghijklmnopqrstuvwxyz"
#used for shifting certain charcaters during encryption and decryption

chatLog = ['CHATSEND']
#starting chat log list with the message identifier

#-----------------------------------------------------------------

def checkFiles():

    with open('usernames.txt') as file:
        usernames = file.read().split('\n')
        usernames = [x for x in usernames if x]
    with open('passwords.txt') as file:
        passwords = file.read().split('\n')
        passwords = [x for x in passwords if x]
    #opens and splits both usernames and passwords at line breaks and saves to lists

    with open('KEYpublics.txt') as file:
        publics = file.read().split('\n/\n')
        publics = [x for x in publics if x]
    with open('KEYprivates.txt') as file:
        privates = file.read().split('\n/\n')
        privates = [x for x in privates if x]
    #opens and splits both public and private at slashes '/' and saves to lists
    
    return usernames,passwords,publics,privates
    #returns all of the up-to-date users information when the function is run

#

def receive(message,index): #takes the data and index of the client sending the message
   
    dataString = message.decode("utf-8")
    dataString = dataString[1:-1].replace("'", "")
    dataList = dataString.split(", ")

    #splits data message sent as a string and turns into list
   
    if dataList[0] == 'login': 
    #checks specific message identifier, and runs respective function
        loginCheck(dataList,index) 
        #both the data and index of client is sent, that currently handling
    elif dataList[0] == 'register':
        registerCheck(dataList,index)
    elif dataList[0] == 'encrypt':
        encrypt(dataList,index)
    elif dataList[0] == 'decrypt':
        decrypt(dataList,index)
    elif dataList[0] == 'keyreq':
        savePublicK(dataList,index)
    elif dataList[0] == 'chatreq':
        sendChat(index)
        #as chat request is a single function and doesn't require anything from the client, just index is sent
    elif dataList[0] == 'send':
        sendMessage(dataList,index)

#

def collect():
    while True:
        client, address = server.accept()
        #server listens for connections and takes clients IP
        print(f'Connected with {str(address)}') #outputs on server
        clients.append(client) 
        #and adds client to client list, in order to manage them when leaving

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()
        #begins the handling thread so the server can continously manage mutliple clients

#

def handle(client):
    while True:
        try:
            index=clients.index(client)
            #getting client index from the client list
            message=client.recv(1024) #1024 bytes
            receive(message,index) #runs receive function for client while they're connected
        except:
            if client!='': #makes sure client hasn't already been removed
                index=clients.index(client)
                clients.pop(index)
                client.close
                #closes and removes client that has left from client list
                client=''
                print('Client',index,'left the server!')

#

def loginCheck(dataList,index):
    usernames,passwords,publics,privates = checkFiles()
    #requests most updated versions of user information files

    username = dataList[1]
    password = dataList[2]
    #username and password entered by client when log in button pressed

    print(dataList)
   
    if username in usernames and username!='': 
    #checks that username is in username list and also isn't empty
        place=usernames.index(username)
        if password==passwords[place]:
        #checks that index of the password is correct for the index of the username
            message = ['USERNAMES'] + usernames
            print(message)
            #when succesfully logged in, list of usernames for public key copying are sent
            for client in clients:
                client.sendall(bytes(str(message), "utf-8"))
                #sending to all users to update for already logged in users
           
            message = ['LOGGEDIN',privates[place]]
            print(message)
            clients[index].sendall(bytes(str(message), "utf-8"))
            #message identifier and specific users private is sent to client
           
        else: #if password isn't correct for username index
            message = ['Incorrect password!']
            print(message)
            clients[index].sendall(bytes(str(message), "utf-8"))
    else: #if username not in the usernames list taken from usernames.txt file
        message = ['Username not registered!']
        print(message)
        clients[index].sendall(bytes(str(message), "utf-8"))

#
   
def registerCheck(dataList,index):
    print(dataList)
    usernames,passwords,publics,privates = checkFiles()
    #files are again checked to get the most up-to-date usernames list

    username = dataList[1]
    password1 = dataList[2]
    password2 = dataList[3]

    if username not in usernames and username.isspace()==False:
    #checks if username is not already in the username list and therefore taken
    #also checks the entered username is not blank
        if password1!=password2:
            message = ['Passwords do not match!']
            print(message)
            clients[index].sendall(bytes(str(message), "utf-8"))
        elif password1==emptyPassword or password2==emptyPassword:
        #empty password assigned value before ('' through sha256)
            message = ['Password cannot be empty!']
            print(message)
            clients[index].sendall(bytes(str(message), "utf-8"))
        else: #succesful account registering
            publicKtoadd,privateKtoadd,keyID=prodKey()
            #as account has just been created, new key pair is made
            with open('usernames.txt','a') as file:
                file.write('\n'+username)
            with open('passwords.txt','a') as file:
                file.write('\n'+password1)
            with open('KEYpublics.txt','a') as file:
                file.write('\n/\n'+publicKtoadd)
            with open('KEYprivates.txt','a') as file:
                file.write('\n/\n'+privateKtoadd)
            #new account credenitals are added to their respective files

            message = ['REGISTERED'] #client code receives succesful registration
            print(message)
            clients[index].sendall(bytes(str(message), "utf-8"))

    else: #if username already in usernames list from file
        message = ['Username not available!']
        print(message)
        clients[index].sendall(bytes(str(message), "utf-8"))

#

def prodKey():
#PUBLIC---
    publicKtoadd='-----BEGIN S.N PUBLIC KEY BLOCK-----\n\n'
    for i in range(PGPlen):
        publicKtoadd+=str(rdi(0,9)) 
        #makes key by repeated random numbers
    publicKtoadd+='\n-----END S.N PUBLIC KEY BLOCK-----\n'

#PRIVATE---
    privateKtoadd='-----BEGIN S.N PRIVATE KEY BLOCK-----\n\n'
    privateKtoadd+=publicKtoadd[KEYBLOCKLEN:KEYBLOCKLEN+keyLen] 
    #takes key ID part of public key and adds to private key
    part=publicKtoadd[(KEYBLOCKLEN+keyLen):(PGPlen+KEYBLOCKLEN)]
    #splits key block and key ID off main body of public key, and adds to private string
    privateKtoadd+=part[len(part)::-1] #reverses key
    privateKtoadd+='\n-----END S.N PRIVATE KEY BLOCK-----\n'

#
    keyID=publicKtoadd[KEYBLOCKLEN:KEYBLOCKLEN+keyLen]
    return publicKtoadd,privateKtoadd,keyID #returns key pair when a new user registers

def encrypt(dataList,index):
    text = dataList[1]
    PGPc = dataList[2]
    #users message and public key to encrypt with are received by server

    PGPc=PGPc[keyLen:]
    #removing key identifier
    print(text)
    print(PGPc)
   
    encryptedMessage=''
    encryptBy=0
   
    if len(text)!=0: #message isn't empty
        if len(text)<=128: #message isn't too long
            if len(PGPc)==246: #valid key entered #256 - keyLen
                for char in text:
                    key=int(PGPc[encryptBy]) 
                    #using the characters in key to shift text
                    if char in shift:
                        position = shift.find(char)
                        new_position = (position + key) % 26
                        new_character = shift[new_position]
                        encryptedMessage += new_character
                        #simple ceaser shift algorithm that moves along the charcater
                        #using the 'shift' string abcdef...
                    else:
                        #if character not shiftable
                        encryptedMessage += char
                    encryptBy+=1 #moves to next character in message
                ogTextLen=len(encryptedMessage)
                count=0
                for i in range(ogTextLen): #repeats for each character in original message
                    for x in range(int(PGPc[i])): 
                        #repeats the number currently parsed in the key
                        ins=fillList[rdi(0,len(fillList)-1)]
                        place=i+x+count
                        #takes a random charcater from fillList and counts the place at which its inserted
                        encryptedMessage=encryptedMessage[:place]+ins+encryptedMessage[place:]
                    count+=int(PGPc[i])
                    #increase the place count by the number just repeated from key
                encryptedMessage+=' '
                encryptedMessage=('-----BEGIN S.N MESSAGE-----\n\n'+
                                  encryptedMessage+
                                  '\n-----END S.N MESSAGE-----\n')
                #adds key block around now encrypted message
                message = ['ENCRYPTED',encryptedMessage]
                #sends message identifier and the message to the client who encrypted
                print(message)
                clients[index].sendall(bytes(str(message), "utf-8"))

            else: #if not 256 character key
                message = ['Invalid public key!']
                print(message)
                clients[index].sendall(bytes(str(message), "utf-8"))

        else:
            message = ['Character limit exceeded!']
            print(message)
            clients[index].sendall(bytes(str(message), "utf-8"))

    else:
        message = ['Message cannot be empty!']
        print(message)
        clients[index].sendall(bytes(str(message), "utf-8"))

#

def decrypt(dataList,index):
    text = dataList[1]
    PGPc = dataList[2]

    print(text)
    print(PGPc)
   
    numbersParsed=0
    addCheck=0
    while addCheck<len(text):
        addCheck+=int(PGPc[numbersParsed])+1
        #sum of all numbers in key length up til it is the same as the length of the message
        numbersParsed+=1
        #1 also added every iteration for actual character from message
    for x in range(numbersParsed):
        for i in range(int(PGPc[x])):
            text = text[0 : x: ] + text[x+1  : :]
            #removing character from text at position x (getting rid of fill list)
    decryptedMessage=''
    decryptBy=0
    for char in text:
        key=int(PGPc[decryptBy])
        #parsing through fill list cleared message and taking number from parsed private key
        if char in shift:
            position = shift.find(char)
            new_position = (position - key) % 26
            new_character = shift[new_position]
            decryptedMessage += new_character
        else:
            decryptedMessage += char
        #shifting backwards along the 'shift' string to reverse ceaser shift
        decryptBy+=1
       
    message = ['DECRYPTED',decryptedMessage]
    print(message)
    clients[index].sendall(bytes(str(message), "utf-8"))

#

def savePublicK(dataList,index):
    usernames,passwords,publics,privates = checkFiles()
    #files are checked for latest update when a public key is requested
    usernameP = dataList[1]
    place=usernames.index(usernameP)
    #index of user selected is taken
    pubKey = publics[place]
    #and public key of same index is sent back to user from publics list
    message = ['PUBLICKEY',pubKey]
    print(message)
    clients[index].sendall(bytes(str(message), "utf-8"))

#

def sendChat(index):
    message = chatLog.copy()
    for client in clients:
        client.sendall(bytes(str(message), "utf-8"))
        #sending the updated chat log to all users
    
#

def sendMessage(dataList,index):
    global chatLog
    username = dataList[1]
    message = (dataList[2])[:-2]
    #getting rid of text widget line break '\n'

    message = message.split('\\n')
    messageLines = ''
    for line in message:
        messageLines += line + '\n'
        #replacing line breaks characters from socket with normal line breaks
   
    print(username+': '+messageLines)
    chatLog.append(username)
    chatLog.append(messageLines)
    #chatLog list apended to with username of client who sent their message, and the message
    sendChat(index) #sent to all users

#-----------------------------------------------------

print(f'Server running on IP: {host}')
collect() #runs main listening loop