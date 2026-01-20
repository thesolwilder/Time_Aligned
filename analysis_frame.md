# Analysis Frame

## customizable
There should be a grid that can be arranged how the user likes it
showing the appropriate date(s) by sphere(s)/project(s)/break(s)
once set up it stays that way.
there is a button to reset it back to default
able to hide or drag smaller the break/idle data

### standard date filters
- by date
- by date range
- by sessions
- all time
- last two weeks
- last 14 days
- last 7 days
- last business week
- this business week

#### default date filters showing
    be able to select a multiple of date windows to show
    for example always show active period by project
        1. all time
        2. last two weeks
        3. this week


### spheres 
- show all byt date filters
- show varying amount of projects/breaks


### important distinctions
    active period and idle/break periods
    need to see those at the same time
    but customizable to hide either

## design thoughts
i am thinking active time on the left half and break/idle on the right
start out with a window inside the left side. plus button to add more.
first version. 
no more than 4 windows per half. 8 for total
4 active / 4 inactive
they take up the space allowed, if 4 they fit equally inside that space
if 1, they take up the whole space
drop down to select range(s) above the time widgets
above active checkboxes to select all spheres or specific
all projects or specfice projects 
all spheres/ all projects

above inactive time
- all break/idle actions
- only breaks
- only idle
- by custom actions

inactive is filtered by active selection. 
only way to see all break/idle actions for all time is to first filter by
all all spheres/ all projects

underneath the time widgets will be the details
show a  timeline still separated by two columns
by the selected time/projects/action
show sphere>project>time period> duration> comment  on left and on right side is blank row since active
on the next row for break/idle show left side blank and then show 
sphere>project>break action>time period>duration> comment
so it always shows the data and then in each column shows the comment


