# Cloud Deployment Guide

This guide explains how to deploy the Claude Voice STT Server on cloud platforms like AWS, GCP, or Azure.

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐         ┌──────────────────┐
│   Cloud VM      │         │   FastAPI Server      │         │   Claude Code    │
├─────────────────┤         ├──────────────────────┤         ├──────────────────┤
│ • Public IP     │         │ • faster-whisper     │         │ • Receives text  │
│ • Auto-scaling │ ──────▶ │ • Cloud GPU          │ ──────▶ │ • Processes      │
│ • Load balancer │  HTTPS  │ • /transcribe API    │  Text   │ • Displays resp  │
└─────────────────┘         │ • SSL/TLS            │         │                  │
                            │ • Monitoring         │         │                  │
                            └──────────────────────┘         └──────────────────┘
```

## Prerequisites

- Cloud account (AWS/GCP/Azure)
- SSH key pair
- Credit card for GPU instances
- Domain name (optional)

## AWS Deployment

### 1. Create EC2 Instance

```bash
# Launch GPU instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0  # Ubuntu 22.04 LTS
  --instance-type g4dn.xlarge      # 1x NVIDIA T4
  --key-name your-key-pair
  --security-group-ids sg-xxxxxxxx
  --user-data "#!/bin/bash
    sudo apt update
    sudo apt install -y python3-pip python3-venv portaudio19-dev
    sudo useradd -m -s /bin/bash claude
  "
```

### 2. Install Dependencies

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# Switch to claude user
sudo su - claude

# Setup project
cd ~
git clone https://github.com/your-repo/claude-voice-server.git
cd claude-voice-server

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn[standard] faster-whisper pyyaml python-multipart

# Configure for cloud
cat > config.yaml << EOF
model:
  name: "medium"
  device: "cuda"
  compute_type: "float16"
EOF
```

### 3. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Request certificate
sudo certbot --nginx -d your-domain.com

# Create nginx config
sudo tee /etc/nginx/sites-available/claude-voice-server << EOF
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/claude-voice-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Systemd Service

```bash
# Create systemd service
sudo tee /etc/systemd/system/claude-voice-server.service << EOF
[Unit]
Description=Claude Voice STT Server
After=network.target nginx.service

[Service]
Type=simple
User=claude
Group=claude
WorkingDirectory=/home/claude/claude-voice-server
ExecStart=/home/claude/claude-voice-server/venv/bin/python -m uvicorn src.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
Environment=PATH=/home/claude/claude-voice-server/venv/bin:/usr/bin

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable claude-voice-server
sudo systemctl start claude-voice-server
```

## GCP Deployment

### 1. Create VM Instance

```bash
# Create new instance
gcloud compute instances create claude-voice-server \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --image-project=ubuntu-os-cloud \
  --image-family=ubuntu-2004-lts \
  --boot-disk-size=50GB
```

### 2. Setup Firewall

```bash
# Allow HTTPS traffic
gcloud compute firewall-rules create allow-https \
  --allow=tcp:443 \
  --target-tags=voice-server \
  --description="Allow HTTPS traffic"

# Apply tag to instance
gcloud compute instances add-tags claude-voice-server \
  --tags=voice-server
```

### 3. Install Dependencies

Same as AWS steps above, using your GCP instance IP.

## Azure Deployment

### 1. Create VM

```bash
# Create VM with GPU
az vm create \
  --resource-group claude-voice-rg \
  --name claude-voice-server \
  --image Ubuntu2204 \
  --size Standard_NC4as_T4_v3 \
  --generate-ssh-keys
```

### 2. Configure Application Gateway (Optional)

```bash
# Create application gateway
az network application-gateway create \
  --resource-group claude-voice-rg \
  --name claude-gateway \
  --location westus2 \
  --sku Standard_v2 \
  --capacity 2 \
  --http-settings-port 8000 \
  --http-settings-protocol Http \
  --frontend-port 80 \
  --public-ip-address myPublicIP
```

## Monitoring

### CloudWatch (AWS)

```bash
# Create CloudWatch agent config
cat > amazon-cloudwatch-agent.json << EOF
{
  "logs": {
    "metrics_collected": {
      "system": {
        "measurement": ["cpu", "memory", "disk", "network"]
      }
    },
    "log_group_name": "/claude-voice-server",
    "log_stream_name": "{instance_id}"
  }
}
EOF

# Install and configure
sudo apt install amazon-cloudwatch-agent
sudo cp amazon-cloudwatch-agent.json /opt/amazon/cloudwatch-agent/etc/amazon-cloudwatch-agent.json
sudo systemctl restart amazon-cloudwatch-agent
```

### Stackdriver (GCP)

```bash
# Enable Stackdriver
gcloud services enable monitoring.googleapis.com

# Create monitoring workspace
gcloud alpha monitoring workspaces create --organization=your-org-id
```

## Auto-scaling

### AWS Auto-scaling Group

```bash
# Create launch configuration
aws autoscaling create-launch-configuration \
  --launch-configuration-name claude-voice-server-lc \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type g4dn.xlarge \
  --key-name your-key-pair \
  --security-groups sg-xxxxxxxx

# Create auto-scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name claude-voice-server-asg \
  --launch-configuration-name claude-voice-server-lc \
  --min-size 1 \
  --max-size 3 \
  --desired-capacity 1 \
  --availability-zone us-east-1a
```

## Cost Optimization

### Spot Instances (AWS)

```bash
# Create spot instance request
aws ec2 request-spot-instances \
  --spot-price "0.5" \
  --instance-count 1 \
  --launch-specification '{"ImageId":"ami-0c55b159cbfafe1f0","InstanceType":"g4dn.xlarge"}'
```

### Preemptible VMs (GCP)

```bash
# Create with preemption flag
gcloud compute instances create claude-voice-server \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --preemptible
```

## Backup and Recovery

### Daily Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/claude-voice-server"

# Create backup
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/claude-voice-server-$DATE.tar.gz \
  --exclude=venv \
  --exclude=*.pyc \
  ~claude/claude-voice-server/

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/ s3://your-backup-bucket/claude-voice-server/ --recursive

echo "Backup completed: $DATE"
```

### Setup Cron Job

```bash
# Add to crontab
crontab -e

# Run daily at 2 AM
0 2 * * * /home/claude/backup.sh
```

## Troubleshooting

### Common Issues

1. **GPU Not Detected**
   ```bash
   # Check nvidia-smi
   nvidia-smi

   # Install nvidia drivers
   sudo apt install nvidia-driver-510
   ```

2. **Port Conflicts**
   ```bash
   # Check ports
   sudo netstat -tulpn | grep 8000

   # Kill process
   sudo kill -9 <PID>
   ```

3. **SSL Certificate Issues**
   ```bash
   # Renew certificate
   sudo certbot renew

   # Check renewal status
   sudo certbot certificates
   ```

### Health Checks

Create health check endpoint:

```python
# src/health_check.py
from fastapi import FastAPI
import psutil
import torch

app = FastAPI()

@app.get("/health")
async def health_check():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    gpu_available = torch.cuda.is_available()

    return {
        "status": "healthy",
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "gpu_available": gpu_available
    }
```

## Deployment Checklist

- [ ] Create cloud instance with GPU
- [ ] Install system dependencies
- [ ] Clone and setup repository
- [ ] Configure virtual environment
- [ ] Setup SSL certificate
- [ ] Configure reverse proxy
- [ ] Create systemd service
- [ ] Setup monitoring
- [ ] Configure backups
- [ ] Test deployment
- [ ] Document deployment process