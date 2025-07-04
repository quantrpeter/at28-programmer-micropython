deploy:
	mpremote rm :boot.py
	mpremote cp flashWrite.py :flashWrite.py
	mpremote cp flashRead.py :flashRead.py
	mpremote cp dummy.py :dummy.py
	mpremote cp main.py :main.py
	mpremote cp ssd1306.py :ssd1306.py

dummy:
	mpremote exec "import dummy"

read:
	mpremote exec "import flashRead; flashRead.dump_flash(0, 2048)"

write:
	mpremote exec "import flashWrite; flashWrite.write('w 2 0x23 3 0x45')"

writeAll:
	mpremote exec "import flashWrite; flashWrite.write_00_to_ff()"
