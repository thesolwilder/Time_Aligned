# setting frame class

#create widget method
#create frame with row/col incremented so that it automatically shows each method frame when reorder calls in method

    #show buttons called

    #show drop sphere dropdown called

    #load selected sphere called

    #project details called

    #seperator method called

    #break actions and idle settings called

#method - seperator
#creates a line between spheres and break/idle actions settings
#use the row += 1 to make sure it is positioned corectly

#buttons for sphere method

    #create new sphere button
        #creates a unique identifyer so that the name of sphere can be changed but history remains
    #active spheres
        #if true only show active spheres in dropdown
    #all spheres
    #inactive spheres

#method - dropdown for spheres
#create a dropdown widget for selecting spheres
#populate the dropdown with active, all, or inactive spheres based on the selected filter
#big font and width
#default sphere shown as intial value

#method - load selected sphere

    #buttons defualt status
        #if default true show button txt as default. can't press inactive
        #else text value setdefault and create method to set as defualt in settings.json

    #button edit sphere name
        #creates dropdown editable with initital value the name of the sphere that is being edited
        #it is highlighed so user can just type to edit
        #when enter selected pop up box to confrim the change

    #button archive sphere
        #if archived true show button txt as archived. can't press inactive

        #else text value setdefault and create method to set as archived in settings.json

    #button delete sphere
        #deletes sphere and associated projects.. permannent
        #pop up box to confimr deleted
        #call save_date with merge=false

#method - project details

    #buttons
        #create new project button
            #creates a new row in for loop at the top of list with mode editings for that iteration
        #active projects filter
            #when selected it is unpushable and shows up bold text like a tab
        #all projects filter
        #archived projects filter

    #for loop showing projects based on selected filter
        #always shows default project as row 0
        #defaults to active projects
        #project name
            #project name is a unique identifier so that name can change up history remains
        #project note
        #project goal
        #buttons
            #edit/save toggle button
                #if editing it shows save
                #if saved it shows edit
            #default button
                #if true , init value default project
                    #else , set defualt
            #archive button
            #default button



#method - break actions and idle settings
#frame creation with two columns

        #col 0 is idle settings

            #boolean to turn off idle settings
                #makes it so that idle settings never  trigger
                #if doing project that is away from the computer for the majority of period

            #time for idle settings threshold  deault 60 seconds  with a textbox
                #between 1 and reasonable amount of seconds

            #dropdown mins idle until idle turns into break
                #never is an option
                #1min - reasaonable mount of time

        #col 1 is break actions

            #same organization as project details but for break actions
            #break actions not associated with a sphere. they are global




