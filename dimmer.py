import appdaemon.plugins.hass.hassapi as hass

class Dimmer(hass.Hass):

    def initialize(self):
        self.dimmer_input = self.args["input"]
        self.target_entities = self.args["entities"]
        self.timer = None
        # The attribute to dim
        self.dim_attribute = self.args.get("attribute", "brightness")

        self.log("Starting dimmer automation for {}".format(self.dimmer_input))
        self.log("Controlling entities: {}".format(", ".join(self.target_entities)))
        self.listen_state(self.input_updated, entity=self.dimmer_input)

    def input_updated(self, entity, attribute, old, new, kwargs):
        self.log("Change detected in {}: {} -> {}".format(entity, old, new))
        self.cancel_dimmer()

        delta = int(float(new))
        if delta != 0:
            # entities is a dict mapping entity name to last seen dimmer value
            self.update({"entities": {e: None for e in self.target_entities},
                         "delta": delta})

    def cancel_dimmer(self):
        if self.timer:
            self.log("Cancelling dimmer timer")
            self.cancel_timer(self.timer)
            self.timer = None

    def update(self, kwargs):
        # This is using a naive approach that works reasonably well
        # for the general case. It can definitely be improved with
        # more knowledge about the platform. For example, deconz
        # lights can be dimmed nicely using the method in
        # https://community.home-assistant.io/t/there-is-a-good-method-for-dimming-lights-in-deconz/138115
        delta = kwargs["delta"]
        entities = {}
        for e,last in kwargs["entities"].items():
            value = self.get_state(e, attribute=self.dim_attribute) or 0
            self.log("Current {} for {} is {}".format(self.dim_attribute, e, value))
            if value != last:
                entities[e] = value
                value += delta
                self.log("Setting {} to {}".format(self.dim_attribute, value))
                self.call_service("light/turn_on",
                                  entity_id=e, 
                                  transition=1,
                                  **{self.dim_attribute: value})
        if entities:
            self.log("Continuing with {}".format(entities.keys()))
            self.timer = self.run_in(self.update, 1, entities=entities, delta=delta)
        else:
            self.log("Nothing more to dim")
            self.reset_input()

    def reset_input(self):
        """Change the input to the "off" state."""
        self.set_value(self.dimmer_input, 0)
