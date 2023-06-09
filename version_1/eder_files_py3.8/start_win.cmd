@echo off
set startgui=""
set serialno=
set rfm=
set board=

:GETOPTS
if /I "%1" == "-g" set startgui="gui" & goto DOSHIFT
if /I "%1" == "--gui" set startgui="gui" & goto DOSHIFT
if /I "%1" == "-u" set serialno=-u %2 & shift & goto DOSHIFT
if /I "%1" == "--unit" set serialno=--unit %2 & shift & goto DOSHIFT
if /I "%1" == "-r" set rfm=-r %2 & shift & goto DOSHIFT
if /I "%1" == "--rfm" set rfm=--rfm %2 & shift & goto DOSHIFT
if /I "%1" == "-f" set fref=-f %2 & shift & goto DOSHIFT
if /I "%1" == "--fref" set fref=--fref %2 & shift & goto DOSHIFT
if /I "%1" == "-b" set board=-b %2 & shift & goto DOSHIFT
if /I "%1" == "--board" set board=--board %2 & shift & goto DOSHIFT
if /I "%1" == "-h" goto HELP
if /I "%1" == "--help" goto HELP
set serialno=-u %1

:DOSHIFT
shift
if not "%1" == "" goto GETOPTS


pushd .
cd Eder_B

if "%serialno%"=="-u " (
   set serialno=
)
if %startgui%=="gui" (
   cd pythonGUI
   python viewNotebook.py %serialno% %fref% %rfm% %board%
) else (   
   python eder.py %serialno% %fref% %rfm% %board%
)
goto END

:HELP
pushd .
cd Eder_B
python eder.py -h

:END
popd