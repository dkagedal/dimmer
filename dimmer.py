import appdaemon.plugins.hass.hassapi as hass

class Dimmer(hass.Hass):

    def initialize(self):
        self.dimmer_input = self.args["input"]
        self.target_entities = self.args["entities"]
        self.timer = None
        # Speed is the number of value steps per second
        self.delta = self.args.get("speed", 32)
        # The attribute to dim
        self.dim_attribute = self.args.get("attribute", "brightness")

        self.log("Starting dimmer automation for {}".format(self.dimmer_input))
        self.log("Controlling entities: {}".format(", ".join(self.target_entities)))
        self.listen_state(self.dimmer_update, entity=self.dimmer_input)

    def dimmer_update(self, entity, attribute, old, new, kwargs):
        self.log("Change detected in {}: {} -> {}".format(entity, old, new))
        self.cancel_dimmer()
        # entities is a dict mapping entity name to last seen dimmer value
        entities = {e: None for e in self.target_entities}
        if new == "up":
            self.update({"entities": entities, "delta": self.delta})
        elif new == "down":
            self.update({"entities": entities, "delta": -self.delta})

    def cancel_dimmer(self):
        if self.timer:
            self.log("Cancelling dimmer timer")
            self.cancel_timer(self.timer)
            self.timer = None

    def update(self, kwargs):
        delta = kwargs["delta"]
        entities = {}
        for e,last in kwargs["entities"].items():
            value = self.get_state(e, attribute=self.dim_attribute) or 0
            self.log("Current {} for {} is {}".format(self.dim_attribute, e, value))
            if value != last:
                entities[e] = value
                self.set_value(e, value + delta)
        if entities:
            self.log("Continuing with {}".format(entities.keys()))
            self.timer = self.run_in(self.update, 1, entities=entities, delta=delta)
        else:
            self.log("Nothing more to dim")
            self.reset_input()

    def set_value(self, entity_id, value):
        self.log("Setting {} to {}".format(self.dim_attribute, value))
        self.call_service("light/turn_on",
                          entity_id=entity_id, 
                          transition=1,
                          **{self.dim_attribute: value})

    def reset_input(self):
        """Change the input to the "off" state."""
        self.select_option(self.dimmer_input, "off")
