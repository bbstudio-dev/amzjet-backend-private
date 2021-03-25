provider "digitalocean" {
  # You need to set this in your .bashrc
  # export DIGITALOCEAN_TOKEN="Your API TOKEN"
}

resource "digitalocean_droplet" "amzjet-master-vm" {
  image = "ubuntu-18-04-x64"
  name = "amzjet-master"
  region = "${var.region}"
  size = "s-4vcpu-8gb"
  ssh_keys = [
    "${var.ssh_fingerprint}"
  ]

  # Run remote-exec first to ensure the host is ready to accept
  # SSH connection from ansible.
  provisioner "remote-exec" {
      inline = [
          "sudo apt-get install software-properties-common",
          "sudo apt-add-repository universe",
          "sudo apt-get update",
          "sudp apt-get update", # https://github.com/hashicorp/terraform/issues/16656
          "sudo apt-get install -y python python-pip",
      ]

      connection {
          user = "root"
          type = "ssh"
          private_key = "${file(var.ssh_private_key)}"
          timeout = "2m"
      }        
  }

  # Run ansible playbook on the remote host. Note that host key checking is disabled:
  # https://stackoverflow.com/a/23094433
  provisioner "local-exec" {
      working_dir = "${path.module}/../../ansible/single"
      command     = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook main.yml -u root --key-file ${var.ssh_private_key} -i ${self.ipv4_address},"
  }  

  "lifecycle" {
    # Set it to True for production resources.
    "prevent_destroy" = false
  }    
}

# TODO: Create GCS buckets, ensure secrets are provisioned.