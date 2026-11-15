# LTE open work

The October bench series delivered 9 of 10 native EPS packets byte for byte to
Yamcs. Eight runs passed every check. The
[original milestone log](https://github.com/ngrabbs/ember/blob/c2be58ed9124c405872d6643fe1c12ee173a5309/ground/lte/TODO.md)
holds the detailed results and completed tasks.

- [ ] Qualify a periodic EPS burst, repeated attach and recovery, and full-duplex eNodeB performance.
- [ ] Reproduce CE/Msg4 and post-attach failures and regress the candidate OAI fixes.
- [ ] Validate restart behavior between the IHU, LTE Feather, and Walter, including queue recovery and delivery acknowledgments.
- [ ] Measure modem energy and radio performance over representative link conditions, including Doppler and timing.
- [ ] Close spacecraft link, antenna, power, environment, and command security requirements separately from the bench work.

[Operator runbook](README.md) · [Diagnostics and profiles](diagnostics/README.md)
