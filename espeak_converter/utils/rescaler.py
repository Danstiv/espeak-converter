class Rescaler:
    def __init__(
        self, source_scale, target_scale, round_result=False, round_ndigits=None
    ):
        self.source_scale = source_scale
        self.target_scale = target_scale
        self.round_result = round_result
        self.round_ndigits = round_ndigits
        self._normalized_source_scale_end = self.source_scale[1] - self.source_scale[0]
        self._normalized_target_scale_end = self.target_scale[1] - self.target_scale[0]
        self._multiplier = (
            self._normalized_target_scale_end / self._normalized_source_scale_end
        )

    def __call__(self, value, reversed=False):
        if not reversed:
            result = (
                value - self.source_scale[0]
            ) * self._multiplier + self.target_scale[0]
        else:
            result = (
                value - self.target_scale[0]
            ) / self._multiplier + self.source_scale[0]
        if self.round_result:
            result = round(result, self.round_ndigits)
        return result
