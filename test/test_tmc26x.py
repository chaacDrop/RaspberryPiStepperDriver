from RaspberryPiStepperDriver.drivers import StepperDriver
from RaspberryPiStepperDriver.activators.spi import SPI
from RaspberryPiStepperDriver.activators import tmc26x
from RaspberryPiStepperDriver.profiles.rectangle import RectangleProfile

def init():
  try:
    spi_dev = SPI(0, 0)
  except FileNotFoundError:
    # No SPI bus is available. Use a fake
    spi_dev = spi.SPI(None, None)
  driver = StepperDriver(
    activator=tmc26x.TMC26XActivator(
      spi=spi_dev,
      step_pin=18,
      dir_pin=23,
      current=300,
      resistor=150
    ),
    profile=RectangleProfile()
  )
  return (spi_dev, driver)

def test_dump():

  print('REGISTERS')
  for key, value in tmc26x.REGISTERS.items():
    print('  ', key, value, bin(value)[2:])

  print('DRIVER_CONTROL_REGISTER')
  for key, value in tmc26x.DRIVER_CONTROL_REGISTER.items():
    print('  ', key, value, bin(value)[2:])

  spi_dev, driver = init()
  driver.start()

  # Enable or disable chopper current flow
  driver.disable()
  driver.enable()

  print('INITIAL_MICROSTEPPING')
  print('  ', bin(tmc26x.INITIAL_MICROSTEPPING))

  print('driver.driver_control_register_value')
  print('  ', tmc26x.tobin(driver.activator.driver_control_register_value, 20))

  print('MICROSTEP_RESOLUTION')
  print('  ', tmc26x.MICROSTEP_RESOLUTION)

  print('microsteps')
  print('  ', bin(driver.activator.microsteps))

  print('Register Values')
  print('  driver_control_register_value       ', tmc26x.tobin(driver.activator.driver_control_register_value, 20))
  print('  chopper_config_register             ', tmc26x.tobin(driver.activator.chopper_config_register, 20))
  print('  cool_step_register_value            ', tmc26x.tobin(driver.activator.cool_step_register_value, 20))
  print('  stall_guard2_current_register_value ', tmc26x.tobin(driver.activator.stall_guard2_current_register_value, 20))
  print('  driver_configuration_register_value ', tmc26x.tobin(driver.activator.driver_configuration_register_value, 20))

  print('steps left', driver.distance_to_go)
  driver.step(100)
  print('steps left', driver.distance_to_go)

def test_get_current():
  spi_dev, driver = init()
  current = driver.activator.get_current()
  print('current', current)

def test_set_stall_guard_threshold():
  spi_dev, driver = init()
  driver.activator.set_stall_guard_threshold(20, True)
  driver.activator.set_stall_guard_threshold(999, False)

def test_get_stall_guard_threshold():
  spi_dev, driver = init()
  # In range
  t_in = 20
  driver.activator.set_stall_guard_threshold(t_in, True)
  t_out = driver.activator.get_stall_guard_threshold()
  assert(t_in == t_out)
  # FIXME doesnt work correctly
  # out of range
  # t_in = -100
  # driver.set_stall_guard_threshold(t_in, True)
  # t_out = driver.get_stall_guard_threshold()
  # print('stall_guard_threshold', t_in, t_out)
  # assert(t_in == 63)

def dump():
  spi_dev, driver = init()
  debug_last_status(driver)
  debug_last_status(driver, tmc26x.TMC26X_READOUT_STALLGUARD)
  debug_last_status(driver, tmc26x.TMC26X_READOUT_CURRENT)

def debug_last_status(driver, read_status_value=None):
  print('INFO: driver started', driver.activator.started)
  driver.activator.read_status(read_status_value)
  if driver.activator.get_over_temperature() & tmc26x.TMC26X_OVERTEMPERATURE_PREWARING:
    print("WARNING: Overtemperature Prewarning!")
  elif driver.activator.get_over_temperature() & tmc26x.TMC26X_OVERTEMPERATURE_SHUTDOWN:
    print("ERROR: Overtemperature Shutdown!")
  if driver.activator.is_short_to_ground_a():
    print("ERROR: SHORT to ground on channel A!")
  if driver.activator.is_short_to_ground_b():
    print("ERROR: SHORT to ground on channel A!")
  if driver.activator.is_open_load_a():
    print("ERROR: Channel A seems to be unconnected!")
  if driver.activator.is_open_load_b():
    print("ERROR: Channel B seems to be unconnected!")
  if driver.activator.is_stall_guard_reached():
    print("INFO: Stall Guard level reached!")
  if driver.activator.is_stand_still():
    print("INFO: Motor is standing still.")
  readout_config = driver.activator.driver_configuration_register_value & tmc26x.DRIVER_CONTROL_REGISTER['READ_SELECTION_PATTERN']
  value = driver.activator.get_readout_value()
  if readout_config == tmc26x.DRIVER_CONTROL_REGISTER['READ_MICROSTEP_POSTION']:
    print("INFO: Microstep postion phase A: ", value)
  elif readout_config == tmc26x.DRIVER_CONTROL_REGISTER['READ_STALL_GUARD_READING']:
    print("INFO: Stall Guard value:", value)
  elif readout_config == tmc26x.DRIVER_CONTROL_REGISTER['READ_STALL_GUARD_AND_COOL_STEP']:
    stallGuard = value & 0xF
    current = value & 0x1F0
    print("INFO: Approx Stall Guard:", stallGuard)
    print("INFO: Current level", current)

if __name__ == '__main__':
  test_dump()
  test_get_current()
  test_set_stall_guard_threshold()
  test_get_stall_guard_threshold()
  dump()
