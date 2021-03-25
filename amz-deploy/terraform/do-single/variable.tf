variable "ssh_private_key" {
    default="~/.ssh/amzjet"
}

variable "ssh_fingerprint" {
    # The key must be registered at https://cloud.digitalocean.com/account/security (SSH keys)
    default="e0:fb:72:11:6e:44:f1:46:44:1f:c9:3f:e6:06:2a:ef"
}

variable "region" {
    default="sfo2"
}