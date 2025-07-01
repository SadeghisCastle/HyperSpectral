from ms260i_spectrograph import MS260iUSB

spec = MS260iUSB()

print("Current wavelength:", spec.position)
spec.goto(500.0)
print("Moved to:", spec.position)

#spec.shutter(True)
#print("Shutter closed:", spec.shuttered)

spec.close_shutter()

#spec.shutter()
#print("Shutter open:", not spec.shuttered)
