# Assignment code
# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re

# 1MB buffer size
BUFFER_SIZE = 1000000

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket, bind it to a port and start listening
try:
  # Create a server socket
  # ~~~~ INSERT CODE ~~~~
  s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  # ~~~~ END CODE INSERT ~~~~
  print ('Created socket')
except:
  print ('Failed to create socket')
  sys.exit()

try:
  # Bind the server socket to a host and port
  # ~~~~ INSERT CODE ~~~~
  s.bind((proxyHost,proxyPort))
  # ~~~~ END CODE INSERT ~~~~
  print ('Port is bound')
except:
  print('Port is already in use')
  sys.exit()

try:
  # Listen on the server socket
  # ~~~~ INSERT CODE ~~~~
  s.listen(5) 
  # ~~~~ END CODE INSERT ~~~~
  print ('Listening to socket')
except:
  print ('Failed to listen')




### ACCEPTING CONNECTIONS WHILE LOOP STARTS HERE

# continuously accept connections
while True:
  print ('Waiting for connection...')
  clientSocket = None
  clientAddress = None
  # Accept connection from client and store in the clientSocket
  try:
    # ~~~~ INSERT CODE ~~~~
    clientSocket, clientAddress = s.accept()
    # ~~~~ END CODE INSERT ~~~~
    print ('Received a connection')
  except:
    print ('Failed to accept connection')
    sys.exit()

  # Get HTTP request from client
  # and store it in the variable: message_bytes
  # ~~~~ INSERT CODE ~~~~
  message_bytes = clientSocket.recv(4096)
  # ~~~~ END CODE INSERT ~~~~

  message = message_bytes.decode('utf-8')
  print ('Received request:')
  print ('< ' + message)

  # Extract the method, URI and version of the HTTP client request 
  requestParts = message.split()
  method = requestParts[0]
  URI = requestParts[1]
  version = requestParts[2]

  print ('Method:\t\t' + method)
  print ('URI:\t\t' + URI)
  print ('Version:\t' + version)
  print ('')

  # Get the requested resource from URI
  # Remove http protocol from the URI
  URI = re.sub('^(/?)http(s?)://', '', URI, count=1)

  # Remove parent directory changes - security
  URI = URI.replace('/..', '')

  # Split hostname from resource name
  resourceParts = URI.split('/', 1)
  hostname = resourceParts[0]
  resource = '/'

  if len(resourceParts) == 2:
    # Resource is absolute URI with hostname and  
    resource = resource + resourceParts[1]

  print ('Requested Resource:\t' + resource)

  # Check if resource is in cache
  try:
    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation = cacheLocation + 'default'

    print ('Cache location:\t\t' + cacheLocation)
  
    fileExists = os.path.isfile(cacheLocation)

    #DEBUGGING STATEMENTS
    # print (f"FileExists: {fileExists}")
    # print (f"Cache Location: {cacheLocation}")

    # Check whether the file is currently in the cache
    cacheFile = open(cacheLocation, "r")
    cacheData = cacheFile.readlines()

    print ('Cache hit! Loading from cache file: ' + cacheLocation)
    # ProxyServer finds a cache hit
    # Send back response to client 
    # ~~~~ INSERT CODE ~~~~
    cacheResponse = "HTTP/1.1 200 OK\r\n"
    cacheResponse = "Content-Type: text/html\r\n" #Assuming only text/html types are requested for now
    cacheResponse += "Content-Length: " + str(len(''.join(cacheData))) + "\r\n"
    cacheResponse += "\r\n"
    cacheResponse += ''.join(cacheData)
    clientSocket.sendall(cacheResponse.encode())
    # print(f"CacheData Contents: {repr(cacheData)}")  # Print in a raw format to debug
    # print ("DEBUGGING STATEMENT ^^^\n")
    # ~~~~ END CODE INSERT ~~~~
    cacheFile.close()
    print ('Sent to the client:')
    print ('> ' + ''.join(cacheData)) #Had to change this because of can't concatenate list to str error
  except:
    # cache miss.  Get resource from origin server
    originServerSocket = None
    # Create a socket to connect to origin server
    # and store in originServerSocket
    # ~~~~ INSERT CODE ~~~~
    originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ~~~~ END CODE INSERT ~~~~

    print ('Connecting to:\t\t' + hostname + '\n')
    try:
      # Get the IP address for a hostname
      address = socket.gethostbyname(hostname)
      # Connect to the origin server
      # ~~~~ INSERT CODE ~~~~
      originServerSocket.connect((address, 80))  #Have to pass as tuple
      # ~~~~ END CODE INSERT ~~~~
      print ('Connected to origin Server')

      originServerRequest = ''
      originServerRequestHeader = ''
      # Create origin server request line and headers to send
      # and store in originServerRequestHeader and originServerRequest
      # originServerRequest is the first line in the request and
      # originServerRequestHeader is the second line in the request
      # ~~~~ INSERT CODE ~~~~
      originServerRequest = f"{method} {resource} HTTP/1.1\r\n"
      originServerRequestHeader = f"Host: {hostname}\r\n"
      originServerRequestHeader += f"User-Agent: Python/requests\r\n"
      originServerRequestHeader += "Accept: */*\r\n"
      originServerRequestHeader += "Connection: close"

      # ~~~~ END CODE INSERT ~~~~

      # Construct the request to send to the origin server
      request = originServerRequest + originServerRequestHeader + '\r\n\r\n'

      # Request the web resource from origin server
      print ('Forwarding request to origin server:')
      for line in request.split('\r\n'):
        print ('> ' + line)

      try:
        originServerSocket.sendall(request.encode())
      except socket.error:
        print ('Forward request to origin failed')
        sys.exit()

      print('Request sent to origin server\n')

      # Get the response from the origin server
      # ~~~~ INSERT CODE ~~~~
      originServerResponse = b""
      while True:
        chunk = originServerSocket.recv(4096)
        if not chunk:
          break
        originServerResponse += chunk
      
      print ("Response Received from origin server\n")
      # ~~~~ END CODE INSERT ~~~~

      # Send the response to the client
      # ~~~~ INSERT CODE ~~~~
      #Parsing for debugging purposes
      originServerResponseStr = originServerResponse.decode('utf-8', errors="ignore")
      header_end = originServerResponseStr.find("\r\n\r\n") + 4
      responseHeaders = originServerResponseStr[:header_end]
      responseBody = originServerResponseStr[header_end:]
      status_line = responseHeaders.split("\r\n")[0]  # Example: "HTTP/1.1 301 Moved Permanently"
      status_code = int(status_line.split(" ")[1])  # Extract the status code

      status_line = responseHeaders.split("\r\n")[0]  # Example: "HTTP/1.1 301 Moved Permanently"
      status_code = int(status_line.split(" ")[1])  # Extract the status code

      ## 🔵 HANDLE REDIRECTS (301 & 302)
      if status_code in [301, 302]:
          location_match = re.search(r"Location: (.+?)\r\n", responseHeaders, re.IGNORECASE)
          if location_match:
              new_url = location_match.group(1)
              print(f"Redirecting to: {new_url}")

              new_uri = re.sub(r'^(/?)http(s?)://', '', new_url, count=1)
              new_parts = new_uri.split('/', 1)
              hostname = new_parts[0]
              resource = '/' + new_parts[1] if len(new_parts) == 2 else '/'

              originServerSocket.close()
              print(f"Reconnecting to new location: {hostname}{resource}")

              try:
                  originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                  address = socket.gethostbyname(hostname)
                  originServerSocket.connect((address, 80))
                  
                  originServerRequest = f"{method} {resource} HTTP/1.1\r\n"
                  originServerRequestHeader = f"Host: {hostname}\r\n"
                  originServerRequestHeader += "User-Agent: Python/requests\r\n"
                  originServerRequestHeader += "Accept: */*\r\n"
                  originServerRequestHeader += "Connection: close\r\n\r\n"

                  originServerSocket.sendall((originServerRequest + originServerRequestHeader).encode())
                  continue  

              except OSError as err:
                  print(f"Failed to connect to {hostname}: {err.strerror}")

      ## HANDLE 404 NOT FOUND
      elif status_code == 404:
          print("Origin server returned 404 Not Found.")

          error_response = "HTTP/1.1 404 Not Found\r\n"
          error_response += "Content-Type: text/html\r\n"
          error_response += "Content-Length: 46\r\n"
          error_response += "\r\n"
          error_response += "<html><body><h1>404 Not Found</h1></body></html>"

          clientSocket.sendall(error_response.encode())
          clientSocket.close()
          print("Sent 404 response to client")
          continue

      clientSocket.sendall(originServerResponse)
      # ~~~~ END CODE INSERT ~~~~

      # Create a new file in the cache for the requested file.
      cacheDir, file = os.path.split(cacheLocation)
      print ('cached directory ' + cacheDir)
      if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)
      cacheFile = open(cacheLocation, 'wb')

      # Save origin server response in the cache file
      # ~~~~ INSERT CODE ~~~~
      cacheFile.write(originServerResponse)
      # ~~~~ END CODE INSERT ~~~~
      cacheFile.close()
      print ('cache file closed')

      # finished communicating with origin server - shutdown socket writes
      print ('origin response received. Closing sockets')
      originServerSocket.close()
      
      clientSocket.shutdown(socket.SHUT_WR)
      print ('client socket shutdown for writing')
    except OSError as err:
      print ('origin server request failed. ' + err.strerror)

  try:
    clientSocket.close()
  except:
    print ('Failed to close client socket')
