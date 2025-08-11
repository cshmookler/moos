// Standard includes
#define _DEFAULT_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// External includes
#include <system_state/system_state.h>

int main() {
  int notified = 0;
  double low_battery_threshold = 20.F;

  while (1) {
    syst_battery_list_t *battery_list = syst_get_batteries(NULL);
    unsigned long battery_count =
        syst_battery_list_get_size(battery_list, NULL);
    for (unsigned long idx = 0; idx < battery_count; ++idx) {
      syst_battery_t *battery = syst_battery_list_get(battery_list, idx, NULL);

      double charge = syst_battery_get_charge(battery, NULL);
      syst_battery_status_t status = syst_battery_get_status(battery, NULL);

      if (charge <= low_battery_threshold &&
          (status & syst_battery_status_charging) == 0) {
        if (!notified) {
          char *name = syst_battery_get_name(battery, NULL);
          char *message;
          asprintf(&message,
                   "notify-send -u critical 'Low Battery (%s %.0f%%)'", name,
                   charge);
          system(message);
          free(message);
          free(name);
          notified = 1;
        }
      } else {
        notified = 0;
      }
    }

    syst_battery_list_free(battery_list);

    sleep(1);
  }
}
