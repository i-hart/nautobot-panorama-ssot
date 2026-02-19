from nautobot_ssot.jobs import DataSource, DataTarget
from nautobot_panorama_ssot.diffsync.adapters.nautobot import NautobotAdapter
from nautobot_panorama_ssot.diffsync.adapters.panorama import PanoramaAdapter


class PanoramaSource(DataSource):

    def load(self):
        self.adapter = PanoramaAdapter(
            panorama=self.job.panorama_instance,
            logger=self.job.logger,
        )
        self.adapter.load()


class PanoramaTarget(DataTarget):

    def load(self):
        self.adapter = NautobotAdapter(
            job=self.job,
            sync=self,
        )
        self.adapter.load()


class PanoramaSync(PanoramaSource, PanoramaTarget):
    name = "Panorama ⇄ Nautobot Sync"
    description = "Full firewall SSoT v3 sync"
