import base64
import time
import oci
from oci.core.models import LaunchInstanceDetails, InstanceSourceViaImageDetails, CreateVnicDetails

# Load config
config = oci.config.from_file()
compute = oci.core.ComputeClient(config)

# 🔧 Replace with your actual values:
COMPARTMENT_ID = "ocid1.tenancy.oc1..aaaaaaaafp5ljfquqmrquodnmop3xu2mfphmzfm63cd4xvusvoas6odqt2ga"
SUBNET_ID = "ocid1.subnet.oc1.ap-singapore-1.aaaaaaaawtqbxwcaaejpl53kvql3shqjhfv4mcefbvos5a7vcq5ywm2obc2q"
IMAGE_ID = "ocid1.image.oc1.ap-singapore-1.aaaaaaaavpms5nv7qmalnorgvemrgumiln5en2o6xmxllosxu5cdaqmgycyq"  # Oracle Linux or Ubuntu image OCID
AVAILABILITY_DOMAIN = "fotf:AP-SINGAPORE-1-AD-1"  # e.g. "kIdk:AP-SINGAPORE-1-AD-1"
CHECK_INTERVAL = 60  # seconds

# cloud-init script to auto install bot
cloud_init = """#cloud-config
runcmd:
  - sudo apt-get update -y
  - sudo apt-get install python3-pip git -y
  - git clone https://github.com/Habibaeo/sniper-mexc-bot
  - pip3 install -r /home/opc/sniper-bot/requirements.txt
  - python3 /home/opc/sniper-bot/deployable_trading_bot.py --symbol XYZUSDT --budget 50 --type LIMIT --limit_price 0.0123 --delay 0.2
"""

USER_DATA = base64.b64encode(cloud_init.encode()).decode()

def try_launch():
    details = LaunchInstanceDetails(
        compartment_id=COMPARTMENT_ID,
        availability_domain=AVAILABILITY_DOMAIN,
        shape="VM.Standard.A1.Flex",
        display_name="sniper-bot-server",
        source_details=InstanceSourceViaImageDetails(source_type="image", image_id=IMAGE_ID),
        create_vnic_details=CreateVnicDetails(subnet_id=SUBNET_ID, assign_public_ip=True),
        metadata={"user_data": USER_DATA},
        shape_config={"ocpus": 1, "memory_in_gbs": 6}
    )
    try:
        resp = compute.launch_instance(details)
        instance_id = resp.data.id
        print(f"✅ Instance launched: {instance_id}")
        return instance_id
    except oci.exceptions.ServiceError as e:
        if "Out of host capacity" in e.message:
            print(f"❌ No capacity, retrying in {CHECK_INTERVAL}s...")
        else:
            print("⚠️ OCI error:", e.message)
        return None

if __name__ == "__main__":
    while True:
        instance_id = try_launch()
        if instance_id:
            break
        time.sleep(CHECK_INTERVAL)
    print("🎯 VPS is booting up and provisioning your trading bot!")
