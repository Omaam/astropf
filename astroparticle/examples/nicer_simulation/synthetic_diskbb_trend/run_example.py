"""Example of VAR(1) model.
"""
import time

import numpy as np
import tensorflow as tf
import tensorflow_probability as tfp
from tensorflow_probability import bijectors as tfb
from tensorflow_probability import distributions as tfd

import astroparticle as ap
from astroparticle.examples import tools as extools

apo = ap.experimental.observations
apt = ap.transitions

extools.seaborn_settings(context="notebook")


def set_particle_numbers():
    import sys
    try:
        if sys.argv[1] == "test":
            num_particles = 200
    except IndexError:
        num_particles = 10000
    return num_particles


def main():

    dtype = tf.float32

    # Load observations and true latents.
    observed_values = tf.convert_to_tensor(
        np.loadtxt("data/observations.txt"), dtype=dtype)

    transition = apt.VectorAutoregressive(
        coefficients=[[[0.1, 0.0], [0.0, 0.1]]],
        noise_covariance=tf.constant([[0.3, 0.0], [0.0, 0.3]])**2,
        dtype=dtype)

    bijector = tfb.Blockwise(
            [tfb.Exp(),
             tfb.Exp()]
         )

    @tf.function(jit_compile=False, autograph=False)
    def observation_fn(step, x):
        num_flux_model = 3451
        num_flux_nicer = 1494
        num_flux_output = 10

        x = bijector(x)
        # x = tfb.Blockwise(
        #     [tfb.Exp(),
        #      tfb.Exp()]
        #  )(x)
        x = tf.unstack(x, axis=1)
        response = ap.experimental.observations.ResponseNicerXti()
        rebin = apo.Rebin(
            energy_splits_old=tf.linspace(0.1, 20., num_flux_nicer),
            energy_splits_new=tf.linspace(0.5, 10., num_flux_output+1))

        energy_edges = response.energy_edges
        powerlaw = ap.experimental.observations.PowerLaw(
            energy_edges, x[0], x[1])

        flux = tf.zeros(num_flux_model)
        flux = powerlaw(flux)
        flux = response(flux)
        flux = rebin(flux)
        observation_dist = tfd.Independent(
            tfd.Poisson(flux),
            reinterpreted_batch_ndims=1)

        return observation_dist

    t0 = time.time()
    num_particles = set_particle_numbers()
    [
     particle,
     _,
     log_lik,
     _
    ] = tfp.experimental.mcmc.particle_filter(
        observed_values,
        initial_state_prior=tfd.MultivariateNormalDiag(
            scale_diag=[0.5, 0.5]),
        transition_fn=transition.get_function(),
        observation_fn=observation_fn,
        num_particles=num_particles)

    t1 = time.time()
    print("Inference ran in {:.2f}s.".format(t1-t0))

    latent_values = tf.convert_to_tensor(
        np.loadtxt("data/latents.txt"), dtype=dtype)

    particle = bijector(particle)
    import matplotlib.pyplot as plt
    particle_centers = tfp.stats.percentile(particle, [50], axis=1)
    print(particle_centers)
    fig, ax = plt.subplots(2)
    ax[0].plot(latent_values[:, 0], color="k")
    ax[0].plot(particle_centers[0, :, 0], color="r")
    ax[1].plot(latent_values[:, 1], color="k")
    ax[1].plot(particle_centers[0, :, 1], color="r")
    plt.show()


if __name__ == "__main__":
    main()
