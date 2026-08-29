PROGNAME      = fitter 
#PROGNAME      = pullcurve 
SOURCES = $(wildcard src/*.cxx)


OBJECTS      := $(addprefix obj/,$(notdir $(SOURCES:.cxx=.o)))
ROOTCFLAGS   := $(shell root-config --cflags)
ROOTLIBS     := $(shell root-config --libs)
ROOTGLIBS    := $(shell root-config --glibs)
ROOTLIBS     := $(shell root-config --nonew --libs)
CFLAGS       += $(ROOTCFLAGS)
LIBS         += $(ROOTLIBS)
INCLUDES     += -I./include 

#  #
LIBS         += -lMinuit
LDFLAGS       = -O

#  #
#LIBS        += -lRooFit -lRooFitCore -lRooStats

$(PROGNAME):    $(OBJECTS)
			g++ -o $@ $(OBJECTS) $(LDFLAGS) $(LIBS) 

obj/%.o : src/%.cxx 
		g++ ${CFLAGS} $(INCLUDES) -c -g -o $@ $<

test:
		@echo $(ROOTCFLAGS)

clean:	
		-rm -f ${PROGNAME} ${OBJECTS}
