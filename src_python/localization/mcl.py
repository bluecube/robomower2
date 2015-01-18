import numpy

class MCL:
    _sample_dtype = [
        ('x', numpy.float),
        ('y', numpy.float),
        ('heading', numpy.float),
        ('weight', numpy.float)]

    def __init__(self, config):
        self._samples = numpy.zeros(config["localization"]["default_sample_count"],
                                    dtype=self._sample_dtype)

    def update(self, motion_model, observations):
        # Prediction step
        motion_model.update_samples(self._samples)

        # Correction step
        for observation in observations:
            observation.weight_samples(self._samples)

        self._resample(len(self._samples)); # TODO: Not needed every time

    def _resample(self, new_count):
        new_samples = numpy.empty(new_count)

        weight_sum = numpy.sum(self._samples["weight"])
        unit = weight_sum / new_count
        position = random.uniform(0, unit)

        it = iter(self._samples)
        sample = next(it)

        for i in range(new_count):
            weight = sample["weight"]

            while pos > weight:
                pos -= weight

                sample = next(it)
                weight = sample["weight"]

            new_samples[i] = sample
            new_samples[i]["weight"] = 1
            pos += unit

    def mean(self):
        return {k: numpy.mean(self._samples[k]) for k in ["x", "y", "heading"]}
