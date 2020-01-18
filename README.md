# Dimmer

This is an AppDaemon app for dimming things. There are many such apps,
and the reason this app exists is not that it is better at dimming all
kinds of lights (it isn't), but because of its approach to dimming
control.

## Dimmer Control

The dimmer can dim a given set of lights up and down, and it does so
using a dimmer state that is part of the Home Assistant state machine.
Ideally, this would perhaps be a "dimmer" entity, but for now it's
using an `input_number` as the dimmer state. The input can be in the
zero state to indicate no dimming is taking place, in a positive state
to indicate it's dimming up, and a negative state to indicate it's
dimming down. The actual input value controls how fast dimming
happens. When dimmin reaches an end (saturated) state, the input is
automatically reset to zero.

This way the dimmer state can be controlled from one or more buttons
and also from the Lovelace UI and the API without an explosion of
automations.

## Configuration

There are three parts to the configuration, the AppDaemon app, the
input, and the automation to control the input from physical dimmer
buttons etc.

### The Input

Add this to `configuration.yaml`:

```yaml
input_number:
  bedroom_dimmer:
    name: Bedroom Dimmer
    initial: 0
    min: -30
    max: 30
    step: 30
    mode: slider
```

The `min`, `max`, `step`, and `mode` are not needed to make
automations work, but they make the dimmer much more useful in an
`entities` UI card.

### The app

```yaml
bedroom_dimmer_app:
  module: dimmer
  class: Dimmer
  input: input_number.bedroom_dimmer
  entities:
    - light.bedroom_ceiling_light
    - light.bedroom_window_light
```

This will make the dimmer update the `brightness` attribute of the two
lights every second, by an amount taken from
`input_number.bedroom_dimmer`. It will update them from where they are
and not move them to matching brightness, and they may saturate at
different times.

The app also supports dimming other attributes than `brightness` by providing an `attribute` configuration:

```yaml
temp_dimmer_app:
  module: dimmer
  class: Dimmer
  input: input_number.temp_dimmer
  attribute: color_temp
  entities:
    - light.bedroom
```

It should be possible to use this to change all kinds of atributes
like media player volume etc, but brightness and color temperature
those I have tested.

### Buttons

Hooking up a dimmer button is not a reasonably straightforward
exercise in making Home Assistant automations. It is probably simplest
to use the UI to create a device automation on the "long press" and
"long press release" triggers on the button devices. I have tested
with an IKEA Trådfri on/off switch but any remote should work as long
as you can automate the long press and releas.

Four automations are needed, for the combinations of up/down and
press/release. They should have action that looks similar to thes:

#### Dim up start

```yaml
  action:
    - service: input_number.set_value
      entity_id: input_number.kitchen_dimmer
      data:
        value: 30
```

#### Dim down start

```yaml
  action:
    - service: input_number.set_value
      entity_id: input_number.kitchen_dimmer
      data:
        value: -30
```

#### Dim button release

```yaml
  action:
    - service: input_number.set_value
      entity_id: input_number.kitchen_dimmer
      data:
        value: 0
```

## Related and Future Work

### Simpler automation

If you have many dimmer buttons, creating all those automations is
tedious work that should be automated. This could easily be done using
a second AppDaemon app that takes as configuration pairs of remotes
and dimmer inputs and then automatically wires up button events to
input changes, based on knowledge of different kinds of dimmer
remotes. I would be possible to add that functionality to this app,
but I think it's a separate concern, best handled by a separate app.

### Add to Home Assistant

I think it would make sense to have the functionality in home
assistant proper. If I find the time, I will see if I can create a
component/integration that provides a `dimmer` entity type that has
the dimmer state and the functionality to control the lights and other
attributes.

### Beter dimming

The actual dimmer code could in some cases be much smarter than
calling `light.turn_on` every second with a transition value of 1. But
this works well enough for me for my Hue bridge lights.
