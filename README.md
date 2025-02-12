# Altruist Home Assistant Integration
Home Assistant Integration to connect Altruist sensor locally.

## Installation

**1. Install files**

Clone the [repository](https://github.com/LoSk-p/altruist-homeassistant-integration.git) and copy `custom_components` folder to your Home Assistant config

**2. Restart HA to load the integration into HA.**

**3.1. Discovery**

If any Altruist sensors are on the local network, the integration will automatically discover them and prompt you to add them.

**3.2. Manual**

To manually add an Altruist sensor, you'll need its IP address. Navigate to Settings → Devices & Services → Integrations and click the Add Integration button. Find `Altruist Sensor` in the list, select it, and then enter the sensor's IP address when prompted.
