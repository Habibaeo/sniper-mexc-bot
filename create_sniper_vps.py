import base64
import time
from datetime import datetime
import oci
from oci.exceptions import ServiceError, RequestException
from http.client import RemoteDisconnected
from oci.core.models import LaunchInstanceDetails, InstanceSourceViaImageDetails, CreateVnicDetails, LaunchInstanceShapeConfigDetails

# Load OCI config
config = oci.config.from_file()
compute = oci.core.ComputeClient(config)

# Replace with your values
COMPARTMENT_ID = "ocid1.tenancy.oc1..aaaaaaaafp5ljfquqmrquodnmop3xu2mfphmzfm63cd4xvusvoas6odqt2ga"
SUBNET_ID = "ocid1.subnet.oc1.ap-singapore-1.aaaaaaaawtqbxwcaaejpl53kvql3shqjhfv4mcefbvos5a7vcq5ywm2obc2q"
IMAGE_ID = "ocid1.image.oc1.ap-singapore-1.aaaaaaaavpms5nv7qmalnorgvemrgumiln5en2o6xmxllosxu5cdaqmgycyq"
AVAILABILITY_DOMAIN = "fotf:AP-SINGAPORE-1-AD-1"
CHECK_INTERVAL = 60  # seconds

# Load your SSH public key
ssh_key_path = r'C:\Users\habib\.ssh\id_rsa.pub'
with open(ssh_key_path, 'r') as key_file:
    ssh_key = key_file.read()

# cloud-init to auto install and run your bot
cloud_init = """#cloud-config
runcmd:
  - sudo apt-get update -y
  - sudo apt-get install python3-pip git -y
  - git clone https://github.com/Habibaeo/sniper-mexc-bot /home/opc/sniper-bot
  - pip3 install -r /home/opc/sniper-bot/requirements.txt
 #- python3 /home/opc/sniper-bot/deployable_trading_bot.py --symbol XYZUSDT --budget 50 --type LIMIT --limit_price 0.0123 --delay 0.2
"""
USER_DATA = base64.b64encode(cloud_init.encode()).decode()

# Define instance details
instance_details = LaunchInstanceDetails(
    compartment_id=COMPARTMENT_ID,
    availability_domain=AVAILABILITY_DOMAIN,
    shape="VM.Standard.A1.Flex",
    display_name="sniper-vps",
    shape_config=LaunchInstanceShapeConfigDetails(ocpus=1, memory_in_gbs=6),
    create_vnic_details=CreateVnicDetails(
        subnet_id=SUBNET_ID,
        assign_public_ip=True,
        display_name="sniper-vps-vnic"
    ),
    source_details=InstanceSourceViaImageDetails(
        source_type="image",
        image_id=IMAGE_ID
    ),
    metadata={
        "ssh_authorized_keys": ssh_key,
        "user_data": USER_DATA
    }
)

# Launch loop
print("🚀 Attempting to launch Oracle Cloud VPS...")

while True:
    try:
        response = compute.launch_instance(instance_details)
        instance = response.data
        print(f"✅ Instance launched successfully: {instance.display_name}")
        print(f"🔗 Instance OCID: {instance.id}")
        break

    except ServiceError as e:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if e.status == 500 and "Out of host capacity" in e.message:
            print(f"[{timestamp}] ⏳ No capacity available — retrying in {CHECK_INTERVAL} seconds.")
        else:
            print(f"[{timestamp}] ❌ ServiceError: {e.message} — Retrying in {CHECK_INTERVAL} seconds.")
        time.sleep(CHECK_INTERVAL)

    except (RequestException, RemoteDisconnected) as e:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] 🔌 Network error — retrying in {CHECK_INTERVAL} seconds.")
        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] ❌ Unexpected error: {str(e)} — retrying in {CHECK_INTERVAL} seconds.")
        time.sleep(CHECK_INTERVAL)

print("🎯 VPS is booting up and provisioning your trading bot!")
