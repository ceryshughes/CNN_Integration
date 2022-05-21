## GRID-MAKER.PRAAT
## 414: LOGGING DURATIONS
## Praat script by Kevin Ryan 9/05, comments slightly edited by Kristine Yu for pedagogical clarity
## Parts inspired by Katherine Crosswhite and Jennifer Hay (as indicated)
## Interactive editing removed and 

#### THIS SECTION FOR USER-DEFINED ARGUMENTS #####

## DIRECTORY: name of directory where wav files are (REQUIRED)
## FILENAME_INITIAL_SUBSTRING: to analyze just a subset of wav files in the directory, which start with this substring (OPTIONAL)
## EXTENSION: audio file type, usually .wav (REQUIRED)
## TIER: name of tier to be created (REQUIRED)

form Select directory, file type, and tiers
	sentence Directory laff_vcv_tokens_with_stops\
	sentence Filename_initial_substring_(optional) 
        sentence Extension .wav
        sentence Tier(s) voicing closure vowel notes
endform

###################################################

#### CREATE LIST OF FILES TO ANNOTATE ####
Create Strings as file list... list 'directory$''filename_initial_substring$'*'extension$'
file_count = Get number of strings


#### LOOP OVER FILE LIST
## (this section partly inspired by code by Katherine Crosswhite)

for k from 1 to file_count
     select Strings list
     current$ = Get string... k
     Read from file... 'directory$''current$'
     short$ = selected$ ("Sound")

## Below: look for grid, if found, open it, otherwise make new one
## This section inspired by code by Jen Hay

     full$ = "'directory$''short$'.TextGrid"
     if fileReadable (full$)
  	Read from file... 'full$'
  	Rename... 'short$'
     else
  	select Sound 'short$'
  	To TextGrid... "'tier$'" notes
     endif

## End Jen Hay inspired block

     plus Sound 'short$'
## Allow user to edit textgrid
     Edit
     pause Annotate tiers, then press continue...
     minus Sound 'short$'
## Save text grid to same directory as wav file
     Write to text file... 'directory$''short$'.TextGrid
     select all
     minus Strings list
     Remove
endfor

################################

select Strings list
Remove
clearinfo
echo Done. 'file_count' files annotated.
