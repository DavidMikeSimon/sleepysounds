# define the clientId
clientId = 'client-id-1'

# define connection parameters to MQTT server
mqttHost = '192.168.1.100'
mqttKeepAlive = 120

# define program parameters
# how old of a message will we still accept and process (in seconds)?
maxMessageSkewTime = 30
# how long does the garage take to fully open or close (in seconds)?
garageActionTime = 2

# define the path to the certificates
# certFilePath = 'certs/yourCertificateFileName.pem'
# keyFilePath = 'certs/yourCertificateKeyName.key'
# caBundlePath = 'certs/ca-bundle.pem'

# define authentication variables for MQTT broker
username = ''
password = ''