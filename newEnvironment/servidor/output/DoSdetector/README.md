# Socat Tester
node server: socat TCP-LISTEN:80,fork -
node client: echo "focaccia" | socat - TCP:10.100.0.2:80
	
