targets := $(patsubst %.dia,%.png,$(wildcard *.dia))

all: $(targets)

%.png: %.dia
	dia -t cairo-png -e $@ $<


clean:
	rm -f $(targets)
