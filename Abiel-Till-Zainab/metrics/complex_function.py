# Function under test
def complex_function(x, y):
    if x > 0:
        if y > 0:
            return "x and y positive"
        elif y == 0:
            return "x positive, y zero"
        else:
            return "x positive, y negative"
    elif x == 0:
        if y > 0:
            return "x zero, y positive"
        elif y == 0:
            return "x and y zero"
        else:
            return "x zero, y negative"
    else:
        if y > 0:
            return "x negative, y positive"
        elif y == 0:
            return "x negative, y zero"
        else:
            return "x and y negative"
