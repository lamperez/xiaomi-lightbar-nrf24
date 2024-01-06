Custom integration for the Xiaomi Mi Computer Monitor Light Bar controlled with a low-cost nRF24L01(+) wireless transceiver.

To download, do for example

```sh
  cd $HASS_CONFIG_DIR/custom_components
  svn export --force https://github.com/lamperez/xiaomi-lightbar-nrf24/trunk/homeassistant/custom_components/xiaomi_lightbar
```

The python library is automatically installed. However, one of its dependencies, `pyrf24`, may require some dynamic libraries to be built.
See https://github.com/lamperez/xiaomi-lightbar-nrf24/tree/main#dependencies
