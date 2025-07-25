# GPIO direct hardware

1-wire devices can be [wired directly to the pins of a raspberry pi](https://pinout.xyz/pinout/1_wire), although a 4.7kΩ resistor is also needed.

## w1

Typically managed by linux operative system *w1* module

```
owserver --w1
```

