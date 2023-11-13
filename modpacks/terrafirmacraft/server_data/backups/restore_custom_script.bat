@echo off
set "gsonPath=%~dp0gson-2.8.2.jar"

cd "../mods"
java -cp "AdvancedBackups-forge-1.18-3.3.jar;%gsonPath%" co.uk.mommyheather.advancedbackups.cli.AdvancedBackupsCLI
