import pdftables_api
 
c = pdftables_api.Client('your API key', timeout=(60, 3600))
c.html('filename.pdf', 'filename.html')
 
'''
  install the pdf-tables module using "pip install https://github.com/pdftables/python-pdftables-api/archive/master.tar.gz"
  add the code above replacing the first argument with your api key which you get by signing up at psf tables
  the second argument represents the time allowed to connect to the server and time allowed to convert
  "c.html" represent the output file type
  at the third significant line, the first argument in this case represent the filename.pdf(input file) and the filename.html(output file)
'''
