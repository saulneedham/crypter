# Crypter
A Python program merging client-server functionalities using sockets for secure, end-to-end communication and file encryption. It prioritises user friendly interactions while providing robust, industry standard encryption mechanisms for private messaging in a dynamic chat environment.

## 📘 Included Files

### Core Source Files (`src`)

client.py - The Python source file containing the client-side logic, responsible for user interface, authentication requests, key management, and message encryption/decryption

server.py - The Python source file containing the server-side logic, responsible for managing socket connections, verifying user credentials, and coordinating the chatroom

KEYprivates.txt - Stores the private keys generated for each registered user

KEYpublics.txt - Stores the public keys generated for each registered user

passwords.txt - Stores the SHA256-hashed passwords for all registered user accounts

usernames.txt - Stores the usernames for all registered user accounts

Crypter logo 1 (ICO File) - The logo used for the program

### Documentation & Coursework (`docs`)

Crypter Coursework (Word/PDF) - The formal documentation, including design decisions, main implementation, security analysis, and testing results

Flowcharts, Diagrams, etc - Includes flowcharts showing the general logic of both programs, and a draft image of crypters initial design

## 🛠 Built With

Python

Socket

Threading

Tkinter

SHA256 hashing

Pyperclip
