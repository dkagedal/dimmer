import appdaemon.plugins.hass.hassapi as hass

class Dimmer(hass.Hass):

    def initialize(self):
        self.dimmer_input = self.args["input"]
        self.target_entities = self.args["entities"]
        # The attribute to dim
        self.dim_attribute = self.args.get("attribute", "brightness")

        self.log("Starting dimmer automation for {}".format(self.dimmer_input))
        self.log("Controlling entities: {}".format(", ".join(self.target_entities)))
        self.listen_state(self.activate, entity=self.dimmer_input, old='0.0')

    def activate(self, entity, attribute, old, new, kwargs):
        self.log("Activation detected in {}: {} -> {}".format(entity, old, new))
        # entities is a dict mapping entity name to last seen dimmer value
        self.update({"entities": {e: None for e in self.target_entities}})

    def update(self, kwargs):
        # Delta is the current dimmer activation, by how much to
        # increment (decrement if negative) the attribute value every
        # second.
        delta = int(float(self.get_state(self.dimmer_input)))
        if delta == 0:
            self.log("Dimming stopped")
            return

        # This is using a naive approach that works reasonably well
        # for the general case. It can definitely be improved with
        # more knowledge about the platform. For example, deconz
        # lights can be dimmed nicely using the method in
        # https://community.home-assistant.io/t/there-is-a-good-method-for-dimming-lights-in-deconz/138115
        entities = {}
        for e,last_value in kwargs["entities"].items():
            value = self.get_state(e, attribute=self.dim_attribute) or 0
            if value == last_value:
                self.log("{} {} saturated at {}".format(e, self.dim_attribute, value))
                continue
            entities[e] = value
            new_value = value + delta
            self.log("Updating {} {}: {} -> {}".format(e, self.dim_attribute, value, new_value))
            self.call_service("light/turn_on",
                              entity_id=e, 
                              transition=1,
                              **{self.dim_attribute: new_value})
        if entities:
            self.log("Continuing with {}".format(", ".join(entities.keys())))
            self.run_in(self.update, 1, entities=entities, delta=delta)
        else:
            self.log("Nothing more to dim")
            self.set_value(self.dimmer_input, 0)
