DEVICE='terrans-mac'
HOST='root@${DOMAIN}'
RASPBERRY='pi@10.200.200.2'

.PHONY: install deploy release dns sudo ssh package iptables kubernetes_install k8s dovecot postfix nextcloud nextcloud_resync_file backup app wireguard pihole webhook earney

deploy: auth dns sudo ssh package iptables k8s dovecot postfix nextcloud webhook backup wireguard

release:
ifdef ARGS
	$(eval SECRET := $(shell sops exec-env secrets/webhook.yml 'echo $${DEPLOYER_SECRET}'))
	curl -i -X POST  \
		-H 'Content-Type: application/json' \
		-H 'X-Webhook-Token: '${SECRET}' \
		-d '{ "application_name": "$(ARGS)", "image_tag": "latest" }' \
		-s https://hooks.terranblake.com/hooks/deploy 
endif

install:
	sops -d --extract '["public_key"]' --output ~/.ssh/terranblake_com.pub secrets/ssh.yml
	sops -d --extract '["private_key"]' --output /Volumes/sammy/.ssh/terranblake_com secrets/ssh.yml
	chmod 600 ~/.ssh/terranblake_com*
	grep -q terranblake.com ~/.ssh/config > /dev/null 2>&1 || cat config/ssh_client_config >> ~/.ssh/config

copy-ssh-key:
	ssh-copy-id -i ~/.ssh/terranblake_com.pub root@${DOMAIN}

dns:
	sops -d --output secrets_decrypted/gandi.yml secrets/gandi.yml
	GANDI_CONFIG='secrets_decrypted/gandi.yml' gandi dns update erebe.eu -f dns/erebe.eu.zones
	GANDI_CONFIG='secrets_decrypted/gandi.yml' gandi dns update erebe.dev -f dns/erebe.dev.zones

ssh:
	ssh ${HOST} "cat /etc/ssh/sshd_config" | diff  - config/sshd_config \
		|| (scp config/sshd_config ${HOST}:/etc/ssh/sshd_config && ssh ${HOST} systemctl restart sshd)

sudo:
	scp config/sudoers ${HOST}:/etc/sudoers.d/erebe

package:
	scp wireguard/wireguard-backport.list ${HOST}:/etc/apt/sources.list.d/
	
	# setup sudo permissions for root
	# ssh ${HOST} 'su -'
	# ssh ${HOST} 'apt-get install sudo -y'
	# ssh ${HOST} 'usermod -aG sudo root'

	# get missing keys
	ssh ${HOST} 'sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 04EE7237B7D453EC'
	ssh ${HOST} 'sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 648ACFD622F3D138'

	# install gnupg2 package
	ssh ${HOST} 'apt-get update && apt-get install -y gnupg2'

	ssh ${HOST} 'sudo apt-get update && apt-get install -f -y curl htop mtr tcpdump ncdu vim dnsutils strace iftop wireguard'
	# Enable automatic security Updates
	ssh ${HOST} 'echo "unattended-upgrades unattended-upgrades/enable_auto_updates boolean true" | debconf-set-selections && apt-get install unattended-upgrades -y'
	# IPv6
	# sops -d --output secrets_decrypted/dhclient6.conf secrets/dhclient6.conf
	# scp secrets_decrypted/dhclient6.conf ${HOST}:/etc/dhcp/dhclient6.conf
	# scp config/dhclient6.service ${HOST}:/etc/systemd/system/
	# ssh ${HOST} 'systemctl daemon-reload && systemctl enable dhclient6.service && systemctl restart dhclient6.service'

iptables:	
	# scp config/iptables ${HOST}:/etc/network/if-pre-up.d/iptables-restore
	# ssh ${HOST} 'chmod +x /etc/network/if-pre-up.d/iptables-restore && sh /etc/network/if-pre-up.d/iptables-restore'

kubernetes_agent_install:
	k3sup join --ip ${AGENT_IP} --server-ip ${SERVER_IP} --ssh-key=/Volumes/sammy/.ssh/terranblake_com
	kubectl label node ${K3S_NODE_NAME} dedicated=worker
	kubectl label node ${K3S_NODE_NAME} node-role.kubernetes.io/worker=worker
	
kubernetes_install:
	# ssh ${HOST} 'export INSTALL_K3S_EXEC="--no-deploy traefik --disable-cloud-controller"; \
	# 	curl -sfL https://get.k3s.io | sh -'

	# get k3s config
	scp ${HOST}:/etc/rancher/k3s/k3s.yaml secrets_decrypted/k3s.yml

	# point to correct domain
	sed -i '' 's/127.0.0.1/${DOMAIN}/' secrets_decrypted/k3s.yml

	# encrypt so it can be stored in git repo
	sops --encrypt secrets_decrypted/k3s.yml > secrets/k3s.yml

	rm secrets_decrypted/k3s.yml
	mkdir ~/.kube || exit 0

	# copy config to default location
	sops -d --output ~/.kube/terranblake_com secrets/k3s.yml

	# restart k3s service if something has changed
	# ssh ${HOST} "cat /etc/systemd/system/k3s.service" | diff  - k8s/k3s.service \
	# 	|| (scp k8s/k3s.service ${HOST}:/etc/systemd/system/k3s.service && ssh ${HOST} 'systemctl daemon-reload && systemctl restart k3s.service')

kubernetes_uninstall:
	ssh ${HOST} '/usr/local/bin/k3s-uninstall.sh'

kubernetes_agent_uninstall:
	ssh ${HOST} '/usr/local/bin/k3s-agent-uninstall.sh'

k8s:
	# this sometimes needs to be ran twice
	kubectl apply -f k8s/ingress-nginx-v0.41.0.yml
	kubectl wait --namespace ingress-nginx \
		--for=condition=ready pod \
		--selector=app.kubernetes.io/component=controller \
		--timeout=120s

	# kubectl create namespace cert-manager

	# add pull token to kube-system namespace
	# eval $$(sops -d --output-type dotenv secrets/ghcr.yml) && \
	# 	kubectl create secret docker-registry ghcr-pull-secret \
	# 	--namespace=kube-system \
	# 	--docker-server=ghcr.io \
	# 	--docker-username=terranblake@gmail.com \
	# 	--docker-password=$$TOKEN

	kubectl apply -f k8s/cert-manager-v1.0.4.yml
	kubectl wait --namespace cert-manager \
		--for=condition=ready pod \
		--selector=app.kubernetes.io/component=webhook \
		--timeout=20s

	kubectl apply -f k8s/lets-encrypt-issuer.yml
	kubectl create -f logs/logs.yml

dovecot:
	sops -d --output secrets_decrypted/dovecot.yml secrets/dovecot.yml
	kubectl apply -f secrets_decrypted/dovecot.yml
	kubectl apply -f dovecot/dovecot.yml

postfix:
	sops -d --output secrets_decrypted/fetchmail.yml secrets/fetchmail.yml
	kubectl apply -f secrets_decrypted/fetchmail.yml
	kubectl apply -f postfix/postfix.yml

nextcloud:
	kubectl apply -f nextcloud/config.nginx.site-confs.default.yml
	kubectl apply -f nextcloud/nextcloud.yml

nextcloud_resync_file:
	kubectl exec -t $(shell kubectl get pods -n default -l app=nextcloud -o json | jq .items[].metadata.name) -- sudo -u abc /config/www/nextcloud/occ files:scan --all

backup:
	# credentials for uploading to google drive
	kubectl create configmap gdrive-refresh --from-file ./secrets_decrypted/gdrive.pickle
	kubectl create configmap gdrive-credentials --from-file ./secrets_decrypted/gdrive.json

	kubectl create configmap gdrive-refresh -n earney --from-file ./secrets_decrypted/gdrive.pickle
	kubectl create configmap gdrive-credentials -n earney --from-file ./secrets_decrypted/gdrive.json

	# create all the jobs
	kubectl apply -f backup/jobs/

webhook:
	# webhook ssh key (only needs to be ran the first time)
	cp webhook/webhook.yml secrets_decrypted/; sed -i "s/__DEPLOYER_SECRET__/$$__DEPLOYER_SECRET__/g" secrets_decrypted/webhook.yml

	# create ghcr imagePullSecret for pulling webhook
	eval $$(sops -d --output-type dotenv secrets/ghcr.yml) && \
		kubectl create secret docker-registry ghcr-pull-secret \
		--namespace=default \
		--docker-server=ghcr.io \
		--docker-username=terranblake@gmail.com \
		--docker-password=$$TOKEN

	# deploy webhook using encrypted webhook manifest
	sops exec-file secrets/webhook.yml 'MANIFEST={} && kubectl apply -f $$MANIFEST'

grafana-chart:
	sops -d secrets/grafana.yml | kubectl create -n default -f -
	kubectl create -f grafana

netdata-monitoring:
	kubectl apply -f netdata

apache-superset:
	# this must be done after the earney namespace has been created
	# sops -d secrets/superset.yml | kubectl delete -n earney -f -
	sops -d secrets/superset.yml | kubectl create -n earney -f -
	kubectl create -f superset/

earney:
	# create namespace for all earney services
	# kubectl create -f earney/namespace.yml

	# create webhook for autodeploys
	# cp webhook/webhook.yml secrets_decrypted/; sed -i "s/__DEPLOYER_SECRET__/$$__DEPLOYER_SECRET__$$/g" secrets_decrypted/webhook.yml

	# create secret for postgres configuration and credentials
	# sops -d secrets/postgres.yml | kubectl delete -f -
	# sops -d secrets/postgres.yml | kubectl create -f -
	# sops -d secrets/postgres.yml | kubectl create -n earney -f -

	# create secret for pulling images from github
	eval $$(sops -d --output-type dotenv secrets/ghcr.yml) && \
		kubectl create secret docker-registry ghcr-pull-secret \
		--namespace=earney \
		--docker-server=ghcr.io \
		--docker-username=terranblake@gmail.com \
		--docker-password=$$TOKEN

	kubectl create configmap gdrive-refresh --from-file ./secrets_decrypted/gdrive.pickle -n earney
	kubectl create configmap gdrive-refresh --from-file ./secrets_decrypted/gdrive.pickle

	kubectl create secret generic gdrive-credentials --from-file ./secrets_decrypted/gdrive.json -n earney
	kubectl create secret generic gdrive-credentials --from-file ./secrets_decrypted/gdrive.json

	# create all credentials for earney services
	kubectl create configmap earney-server-config --from-file ./secrets_decrypted/server_default.json -n earney
	kubectl create configmap earney-dashboard-config --from-file ./secrets_decrypted/default.json -n earney
	kubectl create configmap earney-tdameritrade-auth --from-file ./secrets_decrypted/tdameritrade.json -n earney

	kubectl create -f postgres/
	kubectl create -f redis/

	# create all earney services
	kubectl create -f earney/

minecraft-server:
	kubectl create -f minecraft/namespace.yml

	# create secret for pulling images from github
	eval $$(sops -d --output-type dotenv secrets/ghcr.yml) && \
		kubectl create secret docker-registry ghcr-pull-secret \
		--namespace=minecraft \
		--docker-server=ghcr.io \
		--docker-username=terranblake@gmail.com \
		--docker-password=$$TOKEN

	kubectl create -f minecraft/ingress.yml
	kubectl create -f minecraft/tsst/minecraft.yml

minecraft-overviewer:
	kubectl create configmap minecraft-overviewer-config \
		--from-file ./overviewer/overviewer-config.py \
		--namespace minecraft

	kubectl create -f overviewer/overviewer.yml
	kubectl create -f overviewer/map-viewer


tunnel:
	kubectl apply -f wstunnel/wstunnel.yml

wireguard:
	scp ${HOST}:/etc/wireguard/wghub.conf secrets_decrypted/wghub.conf

	# install wg helper
	ssh ${HOST} 'cd /etc/wireguard && wget https://raw.githubusercontent.com/burghardt/easy-wg-quick/master/easy-wg-quick'
	ssh ${HOST} 'cd /etc/wireguard && chmod +x easy-wg-quick'

	# add new client to network
	ssh ${HOST} 'cd /etc/wireguard && wg-quick down ./wghub.conf'
	ssh ${HOST} 'cd /etc/wireguard && ./easy-wg-quick ${DEVICE}'
	scp ${HOST}:/etc/wireguard/wgclient_${DEVICE}.conf secrets_decrypted/wgclient_${DEVICE}.conf
	ssh ${HOST} 'cd /etc/wireguard && systemctl enable wg-quick@wghub && wg-quick up wg-quick@wghub'

	# copy updated vpn config
	scp ${HOST}:/etc/wireguard/wghub.conf secrets_decrypted/wghub.conf
	sops --encrypt secrets_decrypted/wghub.conf > secrets/wghub.conf
	# rm secrets_decrypted/wghub.conf

pihole:
	sops exec-env secrets/wireguard.yml 'cp pihole/wg0.conf secrets_decrypted/; for i in $$(env | grep _KEY | cut -d = -f1); do sed -i "s#__$${i}__#$${!i}#g" secrets_decrypted/wg0.conf ; done'
	rsync --rsync-path="sudo rsync" secrets_decrypted/wg0.conf ${RASPBERRY}:/etc/wireguard/wg0.conf 
	ssh ${RASPBERRY} 'sudo systemctl enable wg-quick@wghub; sudo systemctl restart wg-quick@wg0'
	kubectl apply -f pihole/pihole.yml
