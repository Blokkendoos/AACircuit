#!/bin/sh

# 2020-03-12 Convert AACircuit components library file from *.ini to *.json

# Usage: ./component_ini_to_json.sh > component_de.json

# 1=Deutsch, 2=English
FILE="component1.ini";
DEBUG=${DEBUG:="0"}; # 1=show debug msg

# check the input file
[ ! -r "$FILE" ] &&
    printf "Unable to read the file ($FILE)\n"

gawk \
    -v debug="$DEBUG" \
'

function replace_chars(str) {

	# replace by spaces
	gsub(/[\x00-\x20]|\r/, " ", str);

	# replace with dot "."
#	gsub(/[\0-\177]/, ".", str);
#	gsub(/\192/, ".", str);
#	gsub(/[\192-\199]/, ".", str);
# 	gsub(/[\xB0-\xBF]/, ".", str);
#  	gsub(/[^\x00-\x7F]/, ".", str);
#  	gsub(/[^\x20-\x7F]/, ".", str);

# a range results in "Invalid collation character" error msg "Ongeldig samengesteld teken: /[^?-?]/"
#	gsub(/[\xC0-\xFF]/, ".", str);
#	gsub(/[\xC3B0-\xC3BF]/, ".", str);

 	gsub(/\xC0/, ".", str);
 	gsub(/\xC1/, ".", str);
 	gsub(/\xC2/, ".", str);
 	gsub(/\xC3/, ".", str);
 	gsub(/\xC4/, ".", str);
 	gsub(/\xC5/, ".", str);
 	gsub(/\xC6/, ".", str);
 	gsub(/\xC7/, ".", str);
 	gsub(/\xC8/, ".", str);
 	gsub(/\xC9/, ".", str);
 	gsub(/\xCA/, ".", str);
 	gsub(/\xCB/, ".", str);
 	gsub(/\xCC/, ".", str);
 	gsub(/\xCD/, ".", str);
 	gsub(/\xCE/, ".", str);
 	gsub(/\xCF/, ".", str);

 	gsub(/\xD0/, ".", str);
 	gsub(/\xD1/, ".", str);
 	gsub(/\xD2/, ".", str);
 	gsub(/\xD3/, ".", str);
 	gsub(/\xD4/, ".", str);
 	gsub(/\xD5/, ".", str);
 	gsub(/\xD6/, ".", str);
 	gsub(/\xD7/, ".", str);
 	gsub(/\xD8/, ".", str);
 	gsub(/\xD9/, ".", str);
 	gsub(/\xDA/, ".", str);
 	gsub(/\xDB/, ".", str);
 	gsub(/\xDC/, ".", str);
 	gsub(/\xDD/, ".", str);
 	gsub(/\xDE/, ".", str);
 	gsub(/\xDF/, ".", str);

 	gsub(/\xE0/, ".", str);
 	gsub(/\xE1/, ".", str);
 	gsub(/\xE2/, ".", str);
 	gsub(/\xE3/, ".", str);
 	gsub(/\xE4/, ".", str);
 	gsub(/\xE5/, ".", str);
 	gsub(/\xE6/, ".", str);
 	gsub(/\xE7/, ".", str);
 	gsub(/\xE8/, ".", str);
 	gsub(/\xE9/, ".", str);
 	gsub(/\xEA/, ".", str);
 	gsub(/\xEB/, ".", str);
 	gsub(/\xEC/, ".", str);
 	gsub(/\xED/, ".", str);
 	gsub(/\xEE/, ".", str);
 	gsub(/\xEF/, ".", str);

 	gsub(/\xF0/, ".", str);
 	gsub(/\xF1/, ".", str);
 	gsub(/\xF2/, ".", str);
 	gsub(/\xF3/, ".", str);
 	gsub(/\xF4/, ".", str);
 	gsub(/\xF5/, ".", str);
 	gsub(/\xF6/, ".", str);
 	gsub(/\xF7/, ".", str);
 	gsub(/\xF8/, ".", str);
 	gsub(/\xF9/, ".", str);
 	gsub(/\xFA/, ".", str);
 	gsub(/\xFB/, ".", str);
 	gsub(/\xFC/, ".", str);
 	gsub(/\xFD/, ".", str);
 	gsub(/\xFE/, ".", str);
 	gsub(/\xFF/, ".", str);

	# escape any (JSON) escape "\" chars
	gsub(/\\/, "\\\\", str);
	
	return str
}

function close_gridlines(last) {
    # close the grid-lines list
    if (last == 1)
        printf "]\n";
    else
        printf "],\n";
}

function grid(line, busy) {

    if (busy == 1)
        close_gridlines(0)
    else
        # start a new grid-lines list
        printf "  %sgrid%s: {\n", quote, quote;

    switch (line) {
        case "1":
            dir = "N"
            break
        case 2:
            dir = "E"
            break
        case 3:
            dir = "S"
            break
        case 4:
            dir = "W"
            break
    }
    printf "    %s%s%s: [\n", quote, dir, quote;
}

BEGIN { 
    printf "{\n"
    quote = "\42"  # double-quote char

    component_busy = 0
    component_nr = 1
    grid_busy = 0
    grid_item = 1
    grid_line_printed = 0
    }

END {
    if (component_busy == 1)
        printf "\n";
 
    printf "}\n" 
    }

{ 

  line = replace_chars($0)
  if (debug) print "LINE:", line;

  switch (line) {

    case /^<R>/:
        # start grid
        split($1, s, ">")
        if (debug) print "GRID:", substr(s[1], 2);

        grid_line_printed = 0
        grid_item += 1
        grid(grid_item, grid_busy)

        break

    case /^<[[:alpha:]].*>/:
        # start component

        # split the whole line
        split(line, str, ">")
        name = substr(str[1], 2)
        if (debug) print name;

        if (component_busy == 1)
            # this is a new entry in the component dictionary
            printf ",\n";

        printf "%s%s%s: {\n", quote, name, quote;
        printf "  %sid%s: %s,\n", quote, quote, component_nr++;

        component_busy = 1

        grid_busy = 0
        grid_line_printed = 0
        grid_item = 1
        grid(grid_item, grid_busy)
        
        break

    case /^<\/>/:
        # close component
        if (debug) printf("END: %s\n", $1);

        close_gridlines(1)

        # close the grid dict
        printf "    }\n";

        # close the component dict
        printf "  }";

        break

    default:
        grid_busy = 1

        if (grid_line_printed == 1)
            # close previous grid-line
            printf ",\n";
	
        printf "    %s%s%s", quote, line, quote;
        grid_line_printed = 1
    }

}

' $FILE
