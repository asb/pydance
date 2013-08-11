#Inspired from Powertop po/Makefile

SRC=$(wildcard *.po)
OBJ= $(SRC:.po=.mo)
INST= $(SRC:.po=.inst)
GENERATE= $(SRC:.po=.generate)

translations: $(OBJ)

%.mo: %.po
	msgfmt -o $@  $<

clean:
	rm -f *.mo *~

install: $(OBJ) $(INST)

generate: $(OBJ) $(GENERATE)

%.inst: %.mo
	mkdir -p $(DESTDIR)$(LOCALESDIR)/$*/LC_MESSAGES/
	cp -f $< $(DESTDIR)$(LOCALESDIR)/$*/LC_MESSAGES/pydance.mo

# Just create and generate the files
%.generate: %.mo
	mkdir -p ../mo/$*/LC_MESSAGES/
	cp -f $< ../mo/$*/LC_MESSAGES/pydance.mo
