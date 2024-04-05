node A: socat TCP-LISTEN:80,fork -
node B: echo "focaccia" | socat - TCP:10.100.0.2:80
	
