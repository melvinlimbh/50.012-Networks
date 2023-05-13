# 50.012 network lab 1

from socket import *
import sys, os
import _thread as thread
import shutil

proxy_port=8080
cache_directory = "./cache/"
"""
Code out proxy server, which allows:
1. client to connect to it
	1.1 1 clientsocket
2. connect to web server
	2.1 1 serversocket

Both will send data in bytes to each other

Note that it works only on the same resource
i.e changing to another HTTP source will throw an error
"""

def force_close(s:socket):
	"""
	discards undelivered data after a socket closesd
	"""
	try:
		s.settimeout(0.5)
		while s.recv(1024):
			pass
	except Exception as ex: # i forgot it's either OSError or IOError
		pass
	s.close()


def client_thread(clientFacingSocket):

	clientFacingSocket.settimeout(5.0)

	try:
		message = clientFacingSocket.recv(4096).decode()
		"""
		If the string received is less than 4096 bytes (or char since char = 1 byte), 
		it will loop again and re-check for more data using socket.recv() 
		"""
		msgElements = message.split()
		print(msgElements)
		
		if len(msgElements) < 5 or msgElements[0].upper() != 'GET' or 'Range:' in msgElements:
			# print("non-supported request: " , msgElements)
			#clientFacingSocket.close()
			force_close(clientFacingSocket)
			return

		# Extract the following info from the received message
		#   webServer: the web server's host name
		#   resource: the web resource requested
		#   file_to_use: a valid file name to cache the requested resource
		#   Assume the HTTP request is in the format of:
		#      GET http://www.mit.edu/ HTTP/1.1\r\n
		#      Host: www.mit.edu\r\n
		#      User-Agent: .....
		#      Accept:  ......
		
		resource = msgElements[1].replace("http://","", 1)
	
		hostHeaderIndex = msgElements.index('Host:')
		webServer = msgElements[hostHeaderIndex+1]

		port = 80 # HTTP

		print("webServer:", webServer)
		print("resource:", resource)

		message=message.replace("Connection: keep-alive","Connection: close")
		
		website_directory = cache_directory + webServer.replace("/",".") + "/"

		if not os.path.exists(website_directory):
			os.makedirs(website_directory)
		
		file_to_use = website_directory + resource.replace("/",".")


	except:
		print(str(sys.exc_info()[0]))                                                
		#clientFacingSocket.close()
		force_close(clientFacingSocket)
		return

	# Check wether the file exists in the cache
	try:
		with open(file_to_use, "rb") as f:
			# ProxyServer finds a cache hit and generates a response message
			print("*****Cache HIT*****")
			print("served from the cache")
			while True:
				buff = f.read(4096)
				if buff:
					#Fill in start    
					clientFacingSocket.send(buff)       
					# Fill in end
				else:
					break

	except FileNotFoundError as e:
		print("!!!!! Cache miss !!!!!")          
		try:
			# USING TCP

			# Fill in start         
			# Create a socket on the proxyserver
			# Connect to the socket to port = 80

			serverFacingSocket = socket(AF_INET,SOCK_STREAM)
			serverFacingSocket.connect((webServer,port))
			serverFacingSocket.send(message.encode())
			# Fill in end
			with open(file_to_use, "wb") as cacheFile:
				print("Created cache file.\nWriting to cache....")
				while True:
					# Fill in start   
					buff = serverFacingSocket.recv(4096)
					# Fill in end
					if buff:
						cacheFile.write(buff)
						# Fill in start
						clientFacingSocket.send(buff)
						# Fill in end
					else:
						print("Done.")
						break
		except:
			print(str(sys.exc_info()[0]))

		finally:
			# Fill in start
			force_close(serverFacingSocket) 
			print("serverFacingSocket force closed.")
			#serverFacingSocket.close()
			#print("serverFacingSocket closed.")
			# Fill in end
	except:
		print(str(sys.exc_info()[0]))

	finally:
		# Fill in start
		#clientFacingSocket.close()
		force_close(clientFacingSocket)
		print("clientFacingSocket force closed.")
		#print("Sockets force closed.")     
		# Fill in end


if len(sys.argv) > 2:
	print('Usage : "python proxy.py port_number"\n')
	sys.exit(2)
if len(sys.argv) == 2:
	proxy_port = int(sys.argv[1])

if not os.path.exists(cache_directory):
	os.makedirs(cache_directory)
else: # Clear cache
	print("wiping cache.....")
	shutil.rmtree(cache_directory)
	os.makedirs(cache_directory)
	print("Done.")
	
# Create a server socket, bind it to a port and start listening
"""
WelcomeSocket creates a new TCP connection and manages it
"""
# Fill in start          
welcomeSocket = socket(AF_INET,SOCK_STREAM)
welcomeSocket.bind(("",proxy_port)) 
# set bind address to empty to get a wildcard address, for docker testing
welcomeSocket.listen(1)
# Fill in end

print('Proxy ready to serve at port', proxy_port)

try: 
	while True:
		# Start receiving data from the client

		# Fill in start   
		clientFacingSocket, addr = welcomeSocket.accept()
		# Fill in end

		# print('Received a connection from:', addr)
	
		# the following function starts a new thread, taking the function name as the first argument, and a tuple of arguments to the function as its second argument
		thread.start_new_thread(client_thread, (clientFacingSocket, ))

except KeyboardInterrupt:
	print('bye...')

finally:
	# Fill in start         
	#welcomeSocket.close()
	force_close(welcomeSocket)   
	# Fill in end