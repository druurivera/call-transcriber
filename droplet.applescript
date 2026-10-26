-- Call Transcriber droplet. macOS only (Windows users: use process_call.ps1 instead).
-- Drop an audio file on this app: asks for the prospect name, then runs
-- transcribe + analyze in the background and notifies you when the note is ready.
-- EDIT scriptDir below to wherever you cloned this repo, then rebuild:
--   osacompile -o ~/Desktop/"Call Transcriber.app" ~/call-transcriber/droplet.applescript

on open theFiles
	repeat with anItem in theFiles
		set audioPath to POSIX path of anItem
		set fileName to name of (info for anItem)

		set defaultName to fileName
		try
			set defaultName to text 1 thru -1 of fileName
			set AppleScript's text item delimiters to "."
			if (count of text items of defaultName) > 1 then
				set defaultName to (text items 1 thru -2 of defaultName) as string
			end if
			set AppleScript's text item delimiters to ""
		end try

		set dialogResult to display dialog "Prospect name for this call?" default answer defaultName with title "Call Transcriber" buttons {"Cancel", "Process"} default button "Process"
		if button returned of dialogResult is "Process" then
			set prospectName to text returned of dialogResult

			display notification "Transcribing and analysing in the background. This can take a while for a long call." with title "Call Transcriber" subtitle prospectName

			set scriptDir to "~/call-transcriber" -- EDIT to your own clone path
			set logFile to "/tmp/call-transcriber-" & (do shell script "date +%s") & ".log"
			set shellCmd to "cd " & quoted form of scriptDir & " && ./process_call.sh " & quoted form of audioPath & " " & quoted form of prospectName & " > " & quoted form of logFile & " 2>&1; osacompile_result=$?; if [ $osacompile_result -eq 0 ]; then osascript -e 'display notification \"Note is ready and open.\" with title \"Call Transcriber\" subtitle \"" & prospectName & "\"'; else osascript -e 'display notification \"Something failed, check " & logFile & "\" with title \"Call Transcriber\" subtitle \"" & prospectName & "\"'; fi"

			do shell script "nohup bash -c " & quoted form of shellCmd & " > /dev/null 2>&1 &"
		end if
	end repeat
end open

on run
	display dialog "Drop a call recording (m4a, wav, mp3, whatever ffmpeg reads) onto this app icon." with title "Call Transcriber" buttons {"OK"} default button "OK"
end run
