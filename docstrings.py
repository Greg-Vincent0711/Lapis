saveDocString = '''
    !save location_name "X Y Z"
    Use double quotes for any spaces.
    !save Nether "34 -20 221"
    !save "Nether Hub" "32 121 120"
    ''' 
getDocString = '''
    !get location_name.
    If you save a name as 'Nether', retrive it using !get 'Nether'
    If a name is saved as Nether, retrieve it using !get Nether
    !get "Villager Center" - use double quotes for spaces
    '''
updateDocString = '''
    !update location_name"
'''
deleteDocString = '''
    !delete location_name
'''
listDocString = '''
    See all locations you have saved.
'''
saveImgDocString='''
    Store an image for a saved place.
    Send an attachment when using this function
    !saveImage location_name 
'''

helpDocString = '''
    Everything Lapis can do.
'''
