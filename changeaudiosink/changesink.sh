#!/bin/sh

echo "Setting default sink $1"
pacmd set-default-sink $1

for index in `pacmd list-sink-inputs | grep "^\s*index" | sed -e "s/[^0-9]//g"`; do
	echo "Moving sink iinput $index to sink $1"
        pacmd move-sink-input $index $1;
done

echo "Done"
